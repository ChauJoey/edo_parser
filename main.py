import argparse

from workflow.workflow_manager import WorkflowManager


def main():
    parser = argparse.ArgumentParser(
        description="Process PDFs directly from Google Drive."
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Optional Google Drive folder (URL/gdrive://ID/raw ID). Defaults to config Input.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose progress logs.",
    )
    args = parser.parse_args()

    workflow = WorkflowManager(source=args.source, verbose=not args.quiet)
    workflow.run()


if __name__ == "__main__":
    main()
