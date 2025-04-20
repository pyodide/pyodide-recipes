"""Parse build result of the pyodide build-recipes command"""

import re
import sys
from datetime import timedelta
from pathlib import Path


def parse_total_build_time(content: str) -> str:
    """Parse the total build time from the content string."""
    pattern = "Time elapsed:"

    # Find the line that starts with the pattern prefix
    for line in content.splitlines():
        if pattern in line:
            # find hh:mm:ss format string in the line
            match = re.search(r"(\d+:\d+:\d+)", line)
            if match:
                time_str = match.group(1)
                return time_str

    return "Failed to parse total build time"


def parse_time(time_str: str) -> int:
    """Convert a time string like '1m 2s' to seconds."""
    total_seconds = 0
    if "h" in time_str:
        hours_part, time_str = time_str.split("h", 1)
        total_seconds += int(hours_part.strip()) * 3600

    if "m" in time_str:
        minutes_part, time_str = time_str.split("m", 1)
        total_seconds += int(minutes_part.strip()) * 60
    if "s" in time_str:
        seconds_part = time_str.split("s", 1)[0]
        total_seconds += int(seconds_part.strip())
    return total_seconds


def format_time(seconds: int) -> str:
    """Format seconds as a human-readable time string."""
    if seconds < 60:
        return f"{seconds}s"
    else:
        time_obj = timedelta(seconds=seconds)
        minutes, seconds = divmod(time_obj.seconds, 60)
        if seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {seconds}s"


def parse_build_results(content: str) -> list[tuple[str, int, str]]:
    """Parse build results from the content string."""
    # Regular expression to match build result lines
    pattern = r"\[\d+/\d+\] \(thread \d+\) built (\S+) in (.+?)\s*$"

    results = []
    for line in content.splitlines():
        match = re.search(pattern, line.strip())
        if match:
            package_name = match.group(1)
            time_str = match.group(2)
            seconds = parse_time(time_str)
            results.append((package_name, seconds, time_str))

    return results


def generate_markdown_table(
    results: list[tuple[str, int, str]], sort_by_time: bool = True
) -> str:
    """Generate a markdown table from build results."""
    if sort_by_time:
        # Sort by build time (descending)
        results = sorted(results, key=lambda x: x[1], reverse=True)

    table = "| Package | Build Time |\n"
    table += "|---------|------------|\n"

    for package, _, time_str in results:
        table += f"| {package} | {time_str} |\n"

    return table


def process_build_results(content: str) -> str:
    """Process build results and return formatted markdown output."""
    results = parse_build_results(content)

    # Calculate some statistics
    total_packages = len(results)
    total_build_time = parse_total_build_time(content)

    # Generate markdown output
    output = []
    output.append("# Package Build Results\n")
    output.append(f"Total packages built: {total_packages}")
    output.append(f"Total build time: {total_build_time}\n")

    # Add table of packages sorted by build time
    output.append("<details>")
    output.append("<summary>Package Build Times (click to expand)</summary>\n")
    output.append(generate_markdown_table(results))
    output.append("</details>")

    # Calculate some statistics for quick reference
    if results:
        longest_build = max(results, key=lambda x: x[1])
        output.append(f"\nLongest build: **{longest_build[0]}** ({longest_build[2]})")

        long_builds = [p for p, s, _ in results if s > 600]  # More than 10 minutes
        output.append(f"Packages built in more than 10 minutes: {len(long_builds)}")

    return "\n".join(output)


def main():
    # Read input from file or stdin
    if len(sys.argv) > 1:
        content = Path(sys.argv[1]).read_text()
    else:
        content = sys.stdin.read()

    # Process the content and print the results
    result = process_build_results(content)
    print(result)


if __name__ == "__main__":
    main()
