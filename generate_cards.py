import yaml
import os
import json

# Define the paths to the submodules' YAML files
submodule_yaml_paths = [
    'docs/yamltest/docs_info.yaml'
]

# Define the output markdown file
output_md_path = 'docs/index.md'
tag_data_json_path = 'docs/tag_data.json'

# Initialize the markdown content
cards_md = """
---
title: "ICICLE Training Catalog"
---

<!-- This file is auto-generated by the generate_cards.py script. -->

# ICICLE Training Catalog

Welcome to the ICICLE Training Catalog! Explore our resources and training opportunities through the categories below.

"""

# Data structure to hold all items for tag filtering
tag_data = []

# Process each submodule's YAML file
for submodule_yaml_path in submodule_yaml_paths:
    if os.path.exists(submodule_yaml_path):
        with open(submodule_yaml_path, 'r') as file:
            data = yaml.safe_load(file)

        for category, items in data.items():
            cards_md += f"\n## {category}\n"
            for item in items:
                title = item.get('title', 'No Title')
                description = item.get('description', 'No Description')
                tags = item.get('tags', [])
                # tags_md = ' '.join([f'<a href="/tag.html?tag={tag}" class="tag" data-tag="{tag}">{tag}</a>' for tag in tags]) # Use this for local version
                tags_md = ' '.join([f'<a href="/mkdocs-testing/tag.html?tag={tag}" class="tag" data-tag="{tag}">{tag}</a>' for tag in tags]) # Use this for deployed version
                
                # Add item to tag_data for JSON
                tag_data.append({
                    "title": title,
                    "description": description,
                    "tags": tags
                })
                
                cards_md += f"""
<div class="card">
  <div class="card-header">
    <h2><a href="#">{title}</a></h2>
  </div>
  <div class="card-body">
    <p>{description}</p>
    <div class="tags">
      {tags_md}
    </div>
  </div>
</div>
"""

# Write the markdown content to index.md
with open(output_md_path, 'w') as file:
    file.write(cards_md)

# Write the tag data to a JSON file for use in tag.html
with open(tag_data_json_path, 'w') as file:
    json.dump(tag_data, file, indent=2)
