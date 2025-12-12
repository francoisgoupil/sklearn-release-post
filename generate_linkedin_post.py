#!/usr/bin/env python3
"""
Automated LinkedIn post generator for scikit-learn releases.

This script scrapes release notes and highlights from scikit-learn documentation
and generates a formatted LinkedIn post with statistics and key highlights.
"""

import re
import sys
from urllib.parse import urljoin
from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup


class ReleaseNotesParser:
    """Parser for scikit-learn release notes pages."""
    
    # Tag patterns to match in HTML
    TAG_PATTERNS = {
        'Major Feature': r'Major Feature',
        'Feature': r'Feature',
        'Efficiency': r'Efficiency',
        'Enhancement': r'Enhancement',
        'Fix': r'Fix',
        'API Change': r'API Change',
    }
    
    def __init__(self, version: str):
        """
        Initialize parser for a specific version.
        
        Args:
            version: Version string (e.g., '1.7', '1.8')
        """
        self.version = version
        self.base_url = "https://scikit-learn.org/stable"
        
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse an HTML page."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            sys.exit(1)
    
    def get_release_notes_url(self) -> str:
        """Get the URL for release notes page."""
        return f"{self.base_url}/whats_new/v{self.version}.html#release-notes-{self.version.replace('.', '-')}"
    
    def get_release_highlights_url(self) -> str:
        """Get the URL for release highlights page."""
        version_underscore = self.version.replace('.', '_')
        return f"{self.base_url}/auto_examples/release_highlights/plot_release_highlights_{version_underscore}_0.html"
    
    def find_legend_section(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Find the legend section to exclude from counting."""
        # Look for the legend section - it's usually near the top
        legend_patterns = [
            soup.find('h2', string=re.compile('Legend', re.I)),
            soup.find('div', class_=re.compile('legend', re.I)),
            soup.find('p', string=re.compile('Legend for changelog', re.I)),
        ]
        
        legend = None
        for pattern in legend_patterns:
            if pattern:
                legend = pattern
                break
        
        return legend
    
    def find_main_version_section(self, soup: BeautifulSoup):
        """
        Find the main version section (e.g., Version 1.7.0) and return its boundaries.
        Excludes patch versions (1.7.1, 1.7.2, etc.).
        
        Returns:
            Tuple of (start_element, end_element) or (None, None) if not found
        """
        # Look for the main version heading (e.g., "Version 1.7.0" or "Version 1.7.0#")
        # Headings may have "#" at the end
        main_version_pattern = rf'Version {re.escape(self.version)}\.0#?$'
        main_version_heading = None
        
        # Find all headings and filter manually
        for heading_tag in ['h2', 'h3', 'h1']:
            headings = soup.find_all(heading_tag)
            for heading in headings:
                text = heading.get_text().strip()
                if re.match(main_version_pattern, text, re.I):
                    main_version_heading = heading
                    break
            if main_version_heading:
                break
        
        if not main_version_heading:
            return None, None
        
        # Find the end boundary - the next version heading at the same level
        # Look for headings like "Version 1.7.1", "Version 1.7.2" (patch versions)
        heading_level = main_version_heading.name
        next_version_pattern = r'Version \d+\.\d+\.\d+#?$'
        next_version_heading = None
        
        # Find all headings of the same level after main_version_heading
        all_headings = soup.find_all(heading_level)
        found_start = False
        for heading in all_headings:
            if heading == main_version_heading:
                found_start = True
                continue
            if found_start:
                text = heading.get_text().strip()
                # Check if this is a patch version (e.g., 1.7.1, 1.7.2)
                if re.match(next_version_pattern, text, re.I):
                    # Make sure it's a patch version of the same release, not a new major version
                    if self.version in text:
                        next_version_heading = heading
                        break
        
        # If no patch version found, look for next major version (e.g., "Version 1.8")
        if not next_version_heading:
            try:
                major, minor = map(int, self.version.split('.'))
                parent_version_pattern = rf'Version {major}\.{minor + 1}#?$'
                for heading in all_headings:
                    if heading == main_version_heading:
                        continue
                    text = heading.get_text().strip()
                    if re.match(parent_version_pattern, text, re.I):
                        next_version_heading = heading
                        break
            except (ValueError, IndexError):
                pass
        
        return main_version_heading, next_version_heading
    
    def count_tags_in_content(self, soup: BeautifulSoup) -> Dict[str, int]:
        """
        Count changelog tags in the content, excluding the legend and patch versions.
        Only counts tags from the main version section (e.g., Version 1.7.0).
        
        Returns:
            Dictionary with counts for each tag type
        """
        counts = {tag: 0 for tag in self.TAG_PATTERNS.keys()}
        
        # Find the main version section boundaries
        main_version_start, main_version_end = self.find_main_version_section(soup)
        
        if not main_version_start:
            # Fallback: if we can't find the main version section, count everything
            # but still exclude legend
            main_version_start = soup
            main_version_end = None
        
        # Find the legend section to exclude
        legend = self.find_legend_section(soup)
        legend_list_items = set()
        if legend:
            # Find the list that contains legend items (usually <ul> or <ol> after legend heading)
            legend_list = legend.find_next(['ul', 'ol'])
            if legend_list:
                # Get all list items in the legend list
                legend_list_items = set(legend_list.find_all('li'))
            else:
                # Fallback: find list items that come before the first version heading
                first_version_heading = soup.find(['h1', 'h2'], string=re.compile(r'Version \d+\.\d+', re.I))
                if first_version_heading:
                    # Get all list items that come before the first version heading
                    all_lis_before_version = soup.find_all('li')
                    for li in all_lis_before_version:
                        # Check if this li comes before the first version heading
                        li_prev_headings = li.find_all_previous(['h1', 'h2'], limit=20)
                        if not any(h == first_version_heading for h in li_prev_headings):
                            # This li comes before any version heading, likely part of legend
                            legend_list_items.add(li)
        
        # Count tags directly by searching from the start heading
        # Get all list items after the start heading
        all_lis = list(main_version_start.find_all_next('li'))  # Convert to list to ensure we can iterate multiple times
        
        # Process each list item and count tags directly
        for li in all_lis:
            # Skip if this list item is part of the legend
            if li in legend_list_items:
                continue
            
            item_text = li.get_text()
            
            # Verify this list item belongs to the main version section (1.7.0)
            # by checking that Version 1.7.0 appears in its previous headings
            prev_headings = li.find_all_previous(['h1', 'h2', 'h3'], limit=50)
            belongs_to_main_version = False
            found_other_version = False
            
            for h in prev_headings:
                if h == main_version_start:
                    belongs_to_main_version = True
                    break
                # Check if we hit another version heading before finding 1.7.0
                heading_text = h.get_text().strip()
                if re.match(r'Version \d+\.\d+', heading_text, re.I) and h != main_version_start:
                    found_other_version = True
                    break
            
            # Skip if this item doesn't belong to our version section
            if not belongs_to_main_version:
                # If we found another version section, we can stop entirely
                if found_other_version:
                    break
                continue
            
            # Stop if we've reached the end marker (next version section)
            if main_version_end:
                if any(h == main_version_end for h in prev_headings):
                    break
            
            # Stop if we've reached the contributors section (for last version section)
            if not main_version_end:
                # Check if contributors section appears in previous headings
                found_contributors = False
                for h in prev_headings:
                    heading_text = h.get_text().strip().lower()
                    if 'code and documentation contributor' in heading_text:
                        found_contributors = True
                        break
                if found_contributors:
                    # We've reached the contributors section, stop counting
                    break
            
            # Check for tags in order of specificity (Major Feature before Feature)
            for tag_type in ['Major Feature', 'API Change', 'Feature', 'Efficiency', 'Enhancement', 'Fix']:
                escaped_tag = re.escape(tag_type)
                pattern = r'\b' + escaped_tag + r'\b'
                regex_pattern = r'^\s*' + pattern + r'|sklearn\.\w+.*?' + pattern
                if re.search(regex_pattern, item_text, re.IGNORECASE | re.MULTILINE):
                    counts[tag_type] += 1
                    break
        
        # Strategy 2: Disabled - Strategy 1 (list items) already captures all tag entries correctly
        # Badge elements were causing false positives by matching "Feature" in longer text
        
        return counts
    
    def extract_highlights(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract key highlights from the release highlights page.
        
        Returns:
            List of highlight strings
        """
        highlights = []
        
        # Remove navigation and sidebar elements
        for nav in soup.find_all(['nav', 'header', 'footer', 'aside']):
            nav.decompose()
        
        # Look for the main content area
        main_content = soup.find('div', class_=re.compile(r'section|content|body|document', re.I))
        if not main_content:
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if not main_content:
            main_content = soup
        
        # Strategy 1: Look for headings that might be highlights (h2, h3, h4)
        headings = main_content.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            text = heading.get_text(strip=True)
            # Skip common non-highlight headings
            skip_headings = ['contents', 'navigation', 'related', 'examples', 'download', 
                           'source code', 'gallery', 'previous', 'next', 'on this page']
            if (len(text) > 10 and len(text) < 150 and
                not any(skip in text.lower() for skip in skip_headings) and
                not re.match(r'^[A-Z\s]{2,}$', text)):  # Skip all-caps
                highlights.append(text)
        
        # Strategy 2: Look for list items in the main content
        list_items = main_content.find_all('li')
        for item in list_items:
            text = item.get_text(strip=True)
            skip_patterns = ['skip', 'navigation', 'menu', 'back to top', 'github', 'choose version',
                           'related projects', 'previous', 'next', 'contents']
            if (len(text) > 20 and len(text) < 300 and
                not any(skip in text.lower() for skip in skip_patterns) and
                not re.match(r'^[A-Z\s]{3,}$', text)):  # Skip all-caps navigation
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'^\*\s*|^-\s*|^\d+\.\s*', '', text)
                # Remove common prefixes
                text = re.sub(r'^(feature|enhancement|fix|improvement):\s*', '', text, flags=re.I)
                if text and text not in highlights:
                    highlights.append(text)
        
        # Strategy 3: Look for paragraphs with substantial content
        paragraphs = main_content.find_all('p')
        for para in paragraphs:
            text = para.get_text(strip=True)
            skip_patterns = ['skip', 'navigation', 'menu', 'back to top', 'github', 'choose version',
                           'related projects', 'copyright', 'license']
            if (len(text) > 30 and len(text) < 250 and
                not any(skip in text.lower() for skip in skip_patterns)):
                text = re.sub(r'\s+', ' ', text)
                if text and text not in highlights:
                    highlights.append(text)
        
        # Remove duplicates and limit
        seen = set()
        unique_highlights = []
        for h in highlights:
            h_lower = h.lower()
            if h_lower not in seen:
                seen.add(h_lower)
                unique_highlights.append(h)
        
        return unique_highlights[:7]
    
    def extract_highlights_from_notes(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract highlights from the release notes page itself.
        Looks for major sections and features mentioned.
        """
        highlights = []
        seen_highlights = set()
        
        # Strategy 1: Look for "Release Highlights" section at the top
        release_highlights_heading = soup.find(['h1', 'h2', 'h3'], 
                                              string=re.compile(r'release.*highlight', re.I))
        if release_highlights_heading:
            # Get list items or paragraphs following this heading
            parent = release_highlights_heading.find_parent(['div', 'section']) or release_highlights_heading
            next_items = parent.find_all(['li', 'p'], limit=10)
            for item in next_items:
                text = item.get_text(strip=True)
                if len(text) > 20 and len(text) < 200:
                    # Clean up
                    text = re.sub(r'^\*\s*|^-\s*|^\d+\.\s*', '', text)
                    if text.lower() not in seen_highlights:
                        seen_highlights.add(text.lower())
                        highlights.append(text)
        
        # Strategy 2: Look for major feature entries in changelog
        # Find list items that contain "Major Feature" or important features
        all_list_items = soup.find_all('li')
        for item in all_list_items[:50]:  # Check first 50 items
            item_text = item.get_text()
            
            # Skip if it's a module heading (contains #)
            if '#' in item_text and len(item_text) < 50:
                continue
            
            # Look for Major Feature entries
            if re.search(r'\bMajor Feature\b', item_text, re.I):
                # Extract the description after "Major Feature"
                # Format is usually: "Major Feature description text"
                parts = re.split(r'Major Feature[:\s]+', item_text, flags=re.I, maxsplit=1)
                if len(parts) > 1:
                    desc = parts[1].strip()
                    # Take first sentence or first 150 chars
                    desc = re.split(r'[.!?]\s+', desc)[0]
                    desc = desc[:150].strip()
                    if len(desc) > 20 and desc.lower() not in seen_highlights:
                        seen_highlights.add(desc.lower())
                        highlights.append(desc)
            
            # Look for Feature entries with important keywords
            elif re.search(r'\bFeature\b', item_text, re.I):
                # Extract meaningful feature descriptions
                # Skip if it's just a module name
                if not re.match(r'^sklearn\.\w+', item_text.strip()):
                    # Extract text after "Feature"
                    parts = re.split(r'Feature[:\s]+', item_text, flags=re.I, maxsplit=1)
                    if len(parts) > 1:
                        desc = parts[1].strip()
                        # Look for meaningful descriptions (not just module paths)
                        if len(desc) > 25 and 'sklearn.' not in desc[:30]:
                            desc = re.split(r'[.!?]\s+', desc)[0]
                            desc = desc[:150].strip()
                            if len(desc) > 20 and desc.lower() not in seen_highlights and len(highlights) < 6:
                                seen_highlights.add(desc.lower())
                                highlights.append(desc)
        
        # Strategy 3: Look for section headings that describe major features
        headings = soup.find_all(['h2', 'h3'])
        for heading in headings:
            text = heading.get_text(strip=True)
            # Skip version numbers and navigation
            if re.match(r'Version \d+\.\d+', text) or 'navigation' in text.lower() or '#' in text:
                continue
            
            # Look for feature-related section names
            feature_keywords = ['support', 'array api', 'metadata routing', 'improved', 'enhanced', 
                              'custom', 'plotting', 'migration', 'sparse']
            if any(keyword in text.lower() for keyword in feature_keywords):
                if len(text) > 10 and len(text) < 100 and text.lower() not in seen_highlights:
                    seen_highlights.add(text.lower())
                    highlights.append(text)
        
        return highlights[:6]
    
    def count_contributors(self, soup: BeautifulSoup) -> int:
        """
        Count the number of contributors mentioned in the release notes.
        
        Returns:
            Number of contributors
        """
        # Look for the contributors section heading
        # Usually "Code and documentation contributors" or "Contributors"
        # Try multiple patterns
        contributor_heading = None
        
        # Pattern 1: Look for heading with "Code and documentation contributors"
        patterns = [
            r'code.*documentation.*contributor',
            r'contributor',
            r'thanks.*contributor'
        ]
        
        for pattern in patterns:
            contributor_heading = soup.find(['h2', 'h3', 'h4', 'h5'], 
                                           string=re.compile(pattern, re.I))
            if contributor_heading:
                break
        
        # Pattern 2: Try finding by text content in any element
        if not contributor_heading:
            contributor_text_nodes = soup.find_all(string=re.compile(r'code.*documentation.*contributor', re.I))
            if contributor_text_nodes:
                for node in contributor_text_nodes:
                    parent = node.find_parent(['h2', 'h3', 'h4', 'h5', 'p', 'div'])
                    if parent:
                        contributor_heading = parent
                        break
        
        if not contributor_heading:
            return 0
        
        # Find the content section containing contributor names
        # The names are usually in a paragraph or div following the heading
        contributor_section = None
        
        # Try next siblings (may be a few elements away)
        current = contributor_heading.find_next_sibling(['p', 'div'])
        for _ in range(5):  # Check up to 5 siblings
            if current:
                text = current.get_text()
                # Look for a paragraph/div with many comma-separated names
                if ',' in text and len(text) > 200 and text.count(',') > 10:
                    contributor_section = current
                    break
                current = current.find_next_sibling(['p', 'div'])
            else:
                break
        
        # If not found in siblings, try next elements (not just siblings)
        if not contributor_section:
            current = contributor_heading.find_next(['p', 'div'])
            for _ in range(10):  # Check up to 10 next elements
                if current:
                    text = current.get_text()
                    if ',' in text and len(text) > 200 and text.count(',') > 10:
                        contributor_section = current
                        break
                    current = current.find_next(['p', 'div'])
                else:
                    break
        
        # If still not found, get the parent and look for paragraphs within it
        if not contributor_section:
            parent = contributor_heading.find_parent(['div', 'section', 'article'])
            if parent:
                paragraphs = parent.find_all('p')
                for para in paragraphs:
                    text = para.get_text()
                    if ',' in text and len(text) > 200 and text.count(',') > 10:
                        contributor_section = para
                        break
        
        if not contributor_section:
            return 0
        
        # Get the text containing contributor names
        contributor_text = contributor_section.get_text()
        
        # Extract the list of names - usually starts after "Thanks to" or "Code and documentation contributors:"
        # Remove the heading text if it's in the same element
        contributor_text = re.sub(r'^.*?code.*documentation.*contributor.*?:?\s*', '', contributor_text, flags=re.I)
        contributor_text = re.sub(r'^.*?thanks to.*?:?\s*', '', contributor_text, flags=re.I)
        
        # Remove common prefixes and suffixes
        contributor_text = re.sub(r'^.*?including\s+', '', contributor_text, flags=re.I)
        contributor_text = re.sub(r'\s+who.*$', '', contributor_text, flags=re.I)
        contributor_text = re.sub(r'\s+including.*$', '', contributor_text, flags=re.I)
        
        # Contributors are listed as comma-separated names
        # Handle patterns like "Name1, Name2, Name3, and Name4"
        # Split by commas, but be careful with brackets like "[bot]"
        # First, handle "and" before splitting
        contributor_text = re.sub(r'\s+and\s+', ', ', contributor_text, flags=re.I)
        
        # Split by commas
        names = re.split(r',\s*(?![^[]*\])', contributor_text)
        
        # Clean up names
        names = [name.strip() for name in names if name.strip()]
        
        # Filter out non-name patterns
        filtered_names = []
        skip_words = {'the', 'and', 'or', 'by', 'to', 'of', 'in', 'on', 'at', 'for', 
                     'with', 'from', 'including', 'thanks', 'everyone', 'who', 'has', 'have',
                     'contributed', 'maintenance', 'improvement', 'since', 'version', 'project'}
        
        for name in names:
            name_clean = name.strip()
            # Remove trailing punctuation
            name_clean = re.sub(r'[.,;:]+$', '', name_clean).strip()
            
            # Skip empty or very short names
            if len(name_clean) < 2:
                continue
            
            # Skip if it's a common word
            if name_clean.lower() in skip_words:
                continue
            
            # Skip if it contains digits (except [bot] which is valid)
            if re.search(r'\d', name_clean.replace('[bot]', '')):
                continue
            
            # Skip if it contains HTML/formatting artifacts
            if re.search(r'[<>{}[\]()]', name_clean.replace('[bot]', '')):
                continue
            
            # Skip if it starts with common prefixes
            if name_clean.lower().startswith(('including', 'thanks', 'the ')):
                continue
            
            # Valid name - add it
            filtered_names.append(name_clean)
        
        return len(filtered_names)
    
    def generate_linkedin_post(self) -> str:
        """Generate the LinkedIn post content."""
        # Fetch release notes
        notes_url = self.get_release_notes_url()
        notes_soup = self.fetch_page(notes_url)
        
        # Extract data from release notes
        tag_counts = self.count_tags_in_content(notes_soup)
        contributor_count = self.count_contributors(notes_soup)
        
        # Try to extract highlights from release highlights page
        highlights_url = self.get_release_highlights_url()
        highlights = []
        try:
            highlights_soup = self.fetch_page(highlights_url)
            highlights = self.extract_highlights(highlights_soup)
        except requests.RequestException:
            # If highlights page doesn't exist or fails, that's OK
            pass
        
        # If we didn't get good highlights, try from release notes
        if not highlights or len(highlights) < 3:
            highlights = self.extract_highlights_from_notes(notes_soup)
        
        # Generate post
        post_lines = [
            f"🚀 scikit-learn {self.version} is out 🚀",
            "",
            "A big shoutout to the community of contributors who continue to push open-source machine learning forward ❤️",
            "",
            "✨ Key Highlights:",
            ""
        ]
        
        # Add highlights (format as bullet points)
        for highlight in highlights[:6]:  # Limit to 6 highlights
            # Clean up highlight text
            highlight = highlight.strip()
            if highlight:
                # Remove markdown formatting if present
                highlight = re.sub(r'^\*\s*', '', highlight)
                highlight = re.sub(r'^-\s*', '', highlight)
                post_lines.append(f"▶️ {highlight}")
        
        post_lines.extend([
            "",
            f"🔗 Check the full release highlights: {highlights_url}",
            "",
            f"Discover scikit-learn {self.version} and its:",
            ""
        ])
        
        # Add statistics
        major_features = tag_counts.get('Major Feature', 0)
        features = tag_counts.get('Feature', 0)
        
        # Display Major Features and Features
        # If there are major features, show both: "X new major features and Y new features"
        # Otherwise, just show: "X new features"
        if major_features > 0:
            feature_parts = []
            feature_parts.append(f"{major_features} new major feature{'s' if major_features != 1 else ''}")
            if features > 0:
                feature_parts.append(f"{features} new feature{'s' if features != 1 else ''}")
            post_lines.append(f"🟢 {' and '.join(feature_parts)}")
        elif features > 0:
            post_lines.append(f"🟢 {features} new feature{'s' if features != 1 else ''}")
        
        efficiency = tag_counts.get('Efficiency', 0)
        enhancements = tag_counts.get('Enhancement', 0)
        total_improvements = efficiency + enhancements
        
        if total_improvements > 0:
            improvement_text = []
            if efficiency > 0:
                improvement_text.append(f"{efficiency} efficiency improvement{'s' if efficiency != 1 else ''}")
            if enhancements > 0:
                improvement_text.append(f"{enhancements} enhancement{'s' if enhancements != 1 else ''}")
            post_lines.append(f"🔵 {' & '.join(improvement_text)}")
        
        api_changes = tag_counts.get('API Change', 0)
        if api_changes > 0:
            post_lines.append(f"🟡 {api_changes} API change{'s' if api_changes != 1 else ''}")
        
        fixes = tag_counts.get('Fix', 0)
        if fixes > 0:
            post_lines.append(f"🔴 {fixes} fix{'es' if fixes != 1 else ''}")
        
        if contributor_count > 0:
            post_lines.append(f"👥 {contributor_count} contributor{'s' if contributor_count != 1 else ''} (thank you all!)")
        
        post_lines.extend([
            "",
            f"📖 More details in the changelog: {notes_url}",
            "",
            "You can upgrade with pip as usual:",
            "",
            "pip install -U scikit-learn",
            "",
            "Using conda-forge builds:",
            "",
            "conda install -c conda-forge scikit-learn",
            "",
            "#scikitlearn #MachineLearning #opensource #DataScience #Python #ML"
        ])
        
        return "\n".join(post_lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python generate_linkedin_post.py <version>", file=sys.stderr)
        print("Example: python generate_linkedin_post.py 1.8", file=sys.stderr)
        sys.exit(1)
    
    version = sys.argv[1]
    parser = ReleaseNotesParser(version)
    post = parser.generate_linkedin_post()
    print(post)


if __name__ == "__main__":
    main()

