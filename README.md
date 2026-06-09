# Website Archiver

A multithreaded website crawler designed to recursively download and archive an entire website for offline storage. The crawler follows internal links, preserves site structure, displays real-time download progress, and logs all crawling activity.

![Banner](/assets/banner.png)

---

## How it works

The crawler operates by accepting a starting URL and recursively discovering additional internal links from downloaded content. Each fetched page is processed to extract URLs using a configurable regular expression. Valid URLs are placed into a shared work queue consumed by a pool of concurrent worker threads, each responsible for downloading content, saving it to disk, and optionally parsing further links if the response MIME type matches the configured textual types. Failed requests are retried up to a configurable limit.

### Running

```bash
website_archiver <url> [options]
```

---

## Environment

* Python 3.12+

### Installing dependencies

```bash
uv sync
```

### Setting pre-commit

```bash
uv run poe set-dev
```

### Executing

```bash
uv run poe start <url>
```

---

## Configuration

All configuration is provided via command-line arguments.

| Argument | Default | Description |
| --- | --- | --- |
| `url` | *required* | Starting URL to be crawled by the workers. |
| `-o`, `--output` | `./crawled` | Folder where crawled websites contents are stored. |
| `--logs` | `./logs` | Folder where crawler execution logs are written |
| `--blacklist` | `()` | List of URL patterns that will be excluded from crawling. Any URL matching an entry in this list will not be downloaded or processed (use comma as separator). |
| `--whitelist` | `(".*",)` | List of URL patterns that will be included into crawling. Any URL matching an entry in this list will be downloaded or processed if not matched by a pattern in the blacklist (use comma as separator). |
| `--max-workers` | `32` | Maximum number of concurrent crawler workers. |
| `--max-retries` | `5` | Maximum number of retry attempts for a failed crawl task of a worker. |
| `--invalid-chars` | `[<>:"\|?*]` | Pattern matching URLs inside any valid textual content found. |
| `-s`, `--search` | `"(/[^"]+)"\|href="([^"]+)"` | Pattern matching URLs inside any valid textual content found. |
| `--textual-mimes` | `("text/", "application/javascript", "application/json", "application/xhtml+xml")` | MIME content types that should be treated as text and scanned for additional URLs (use comma as separator). |
| `--restricted-search` | Off | Prevents link discovery for blacklisted URLs. |

---
