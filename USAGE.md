# Usage Guide

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the script with a version number:
```bash
python generate_linkedin_post.py 1.7
```

3. Copy the output and paste it into LinkedIn!

## Example Output

For version 1.7, the script generates:

```
🚀 scikit-learn 1.7 is out 🚀

A big shoutout to the community of contributors who continue to push open-source machine learning forward ❤️

✨ Key Highlights:

▶️ [Highlights extracted from release notes]

🔗 Check the full release highlights: [URL]

Discover scikit-learn 1.7 and its:

🟢 X new features
🔵 Y efficiency improvements & Z enhancements
🟡 N API changes
🔴 M fixes
👥 K contributors (thank you all!)

📖 More details in the changelog: [URL]

[Installation instructions and hashtags]
```

## How It Works

### Tag Counting

The script counts changelog tags by:
1. Finding tag badges/spans in HTML
2. Parsing list items that contain changelog entries
3. Excluding the legend section automatically

Tags counted:
- 🟢 **Major Feature** + **Feature** = "new features"
- 🔵 **Efficiency** + **Enhancement** = "efficiency improvements & enhancements"
- 🟡 **API Change** = "API changes"
- 🔴 **Fix** = "fixes"

### Highlight Extraction

The script tries two approaches:
1. **Release Highlights Page**: Extracts from the dedicated highlights page
2. **Release Notes Page**: Falls back to extracting from major sections and feature descriptions

**Note**: Highlight extraction may need manual refinement. You can edit the generated post to improve highlights.

### Contributor Counting

Finds the "Code and documentation contributors" section and counts unique contributor names.

## Customization

### Manual Highlight Override

If you want to manually specify highlights, you can:
1. Run the script to get the base post
2. Edit the highlights section manually
3. Keep the rest of the statistics

### Adjusting Tag Counts

If tag counts seem incorrect, you can:
1. Check the release notes page manually
2. Adjust the counting logic in `count_tags_in_content()` method
3. The legend exclusion should work automatically

## Troubleshooting

### Empty Highlights

If highlights are empty:
- The release highlights page might have a different structure
- Try manually adding highlights based on the release notes
- Check the release highlights URL in the generated post

### Incorrect Tag Counts

If tag counts seem wrong:
- Verify by manually checking the release notes page
- The script excludes the legend automatically
- Check if the HTML structure has changed

### Contributor Count Issues

If contributor count seems low:
- Check the "Code and documentation contributors" section manually
- The script filters out common words and formatting
- Some contributors might be listed differently

## Tips

1. **Review Before Posting**: Always review the generated post before posting
2. **Verify Statistics**: Check a few tag counts manually to ensure accuracy
3. **Enhance Highlights**: Add or refine highlights based on your knowledge of the release
4. **Test First**: Test with a previous version (like 1.7) to verify output format

## Future Versions

For future scikit-learn releases (1.8, 1.9, etc.):
- The script should work automatically
- URL patterns are version-agnostic
- HTML structure changes may require script updates

