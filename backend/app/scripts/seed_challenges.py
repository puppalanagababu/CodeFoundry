import argparse
import sys
from app.database import get_db_context
from app.services.seed_service import seed_challenges


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed initial CodeFoundry challenge catalog and test cases."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        default=False,
        help="Opt-in synchronization mode: update attributes of existing challenges, test cases, and files.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CodeFoundry Challenge Seeding")
    print(f"Mode: {'Synchronization (--sync)' if args.sync else 'Create-if-missing (Default)'}")
    print("=" * 60)

    try:
        with get_db_context() as db:
            result = seed_challenges(db=db, sync=args.sync)

        created = result.get("created", [])
        updated = result.get("updated", [])
        skipped = result.get("skipped", [])
        total_tc = result.get("total_test_cases", 0)
        total_fl = result.get("total_files", 0)

        if created:
            print("\n[Created Challenges]:")
            for title in created:
                print(f"  + {title}")

        if updated:
            print("\n[Updated Challenges]:")
            for title in updated:
                print(f"  ~ {title}")

        if skipped:
            print("\n[Skipped (Already Exists)]:")
            for title in skipped:
                print(f"  - {title}")

        print("\nSummary:")
        print(f"  Created challenges: {len(created)}")
        print(f"  Updated challenges: {len(updated)}")
        print(f"  Skipped challenges: {len(skipped)}")
        print(f"  Test cases processed: {total_tc}")
        print(f"  Files processed: {total_fl}")
        print("\nChallenge seeding completed successfully.")

    except Exception as exc:
        print(f"\nERROR: Challenge seeding failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
