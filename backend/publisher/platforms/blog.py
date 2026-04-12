"""Blog publisher — writes MDX to soxai website repo and pushes.

Publishing flow:
  1. Generate slug from title
  2. Write MDX file with frontmatter to apps/website/src/content/blog/
  3. Git commit + push
  4. Website auto-rebuilds on push
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from config import settings

# Path to the soxai website blog content
BLOG_DIR = Path("/home/liangbo/dev/soxai/apps/website/src/content/blog")


def slugify(title: str) -> str:
    """Convert title to URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')[:80]


class BlogPublisher:
    """Publish content as MDX blog posts to soxai website."""

    async def publish(self, title: str, body: str, summary: str,
                      tags: list[str] | None = None, language: str = "en") -> str | None:
        """Write MDX file, commit, push. Returns the blog URL or None on failure."""
        try:
            slug = slugify(title)
            filename = f"{slug}.mdx"
            filepath = BLOG_DIR / filename

            if not BLOG_DIR.exists():
                print(f"Blog directory not found: {BLOG_DIR}")
                return None

            # Build frontmatter
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            tag_list = tags or ["ai", "api", "gateway"]
            tags_str = ", ".join(f'"{t}"' for t in tag_list)

            mdx_content = f"""---
title: "{title}"
description: "{summary[:155] if summary else title}"
date: "{date}"
tags: [{tags_str}]
author: SoxAI Team
---

{body}
"""

            # Write file
            filepath.write_text(mdx_content, encoding="utf-8")
            print(f"Blog post written to {filepath}")

            # Git commit + push
            repo_dir = str(BLOG_DIR.parent.parent.parent.parent.parent)  # soxai root
            result = subprocess.run(
                ["git", "add", str(filepath)],
                cwd=repo_dir, capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"git add failed: {result.stderr}")
                return None

            result = subprocess.run(
                ["git", "commit", "-m", f"blog: {title[:60]}"],
                cwd=repo_dir, capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"git commit failed: {result.stderr}")
                # File was written even if commit fails
                return f"https://www.soxai.io/blog/{slug}"

            result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo_dir, capture_output=True, text=True,
            )
            if result.returncode != 0:
                print(f"git push failed: {result.stderr}")

            blog_url = f"https://www.soxai.io/blog/{slug}"
            print(f"Blog published: {blog_url}")
            return blog_url

        except Exception as e:
            print(f"Blog publish failed: {e}")
            return None
