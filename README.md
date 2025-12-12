# Automated LinkedIn Post Generator for scikit-learn Releases

This script automatically generates LinkedIn posts for scikit-learn releases by scraping release notes and highlights from the official documentation.

## Features

- 🎯 Automatically counts changelog tags (Major Feature, Feature, Efficiency, Enhancement, Fix, API Change)
- 📊 Extracts key highlights from release highlights pages
- 👥 Counts contributors mentioned in release notes
- 📝 Generates formatted LinkedIn posts matching your style

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script with a version number:

```bash
python generate_linkedin_post.py <version>
```

### Examples

```bash
# Generate post for version 1.7
python generate_linkedin_post.py 1.7

# Generate post for version 1.8
python generate_linkedin_post.py 1.8
```

The script will:
1. Fetch the release notes page from `https://scikit-learn.org/stable/whats_new/v{version}.html`
2. Fetch the release highlights page from `https://scikit-learn.org/stable/auto_examples/release_highlights/plot_release_highlights_{version}_0.html`
3. Parse and count changelog tags (excluding the legend)
4. Extract key highlights
5. Count contributors
6. Generate a formatted LinkedIn post

## Output

The script outputs a formatted LinkedIn post to stdout that includes:
- Version announcement
- Key highlights (extracted from release highlights page)
- Statistics (features, improvements, API changes, fixes)
- Contributor count
- Links to release notes and highlights
- Installation instructions
- Hashtags

## How It Works

### Tag Counting

The script uses multiple strategies to accurately count changelog tags:

1. **Span/Badge Detection**: Looks for tags in HTML spans, divs, or other badge elements
2. **List Item Parsing**: Examines list items that contain changelog entries
3. **Text Matching**: Falls back to text pattern matching if needed

The legend section is automatically excluded from counts to ensure accuracy.

### Highlight Extraction

Extracts highlights from:
- List items in the main content area
- Paragraphs that appear to be highlight descriptions
- Filters out navigation elements and non-content text

### Contributor Counting

Finds the "Code and documentation contributors" section and:
- Extracts comma-separated names
- Filters out common words and formatting artifacts
- Returns an accurate count

## Customization

You can modify the script to:
- Change the post format/style
- Adjust highlight extraction logic
- Modify tag counting strategies
- Add additional statistics

## Notes

- The script requires internet access to fetch release notes
- HTML structure changes in scikit-learn docs may require script updates
- Tag counting excludes the legend section automatically
- The script handles edge cases like missing sections gracefully

