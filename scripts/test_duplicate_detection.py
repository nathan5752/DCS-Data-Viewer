"""Test script for duplicate detection functionality."""
import sys
from data.data_manager import DataManager

def test_duplicate_detection():
    """Test the duplicate detection in append_data method."""
    print("=" * 60)
    print("Testing Duplicate Detection Functionality")
    print("=" * 60)

    # Initialize data manager
    dm = DataManager()

    # Test 1: Load initial data
    print("\n[Test 1] Loading initial test data...")
    success, message, df = dm.load_excel(
        "test_data.xlsx",
        tag_row=1,
        description_row=2,
        units_row=3,
        data_start_row=4
    )

    if success:
        print(f"  [OK] SUCCESS: {message}")
        print(f"    Timestamp range: {df['Instrument Tag'].min()} to {df['Instrument Tag'].max()}")
    else:
        print(f"  [FAIL] FAILED: {message}")
        return False

    # Test 2: Append data WITH duplicates (should detect and return metadata)
    print("\n[Test 2] Appending data with duplicate timestamps...")
    success, message, result = dm.append_data(
        "test_data_append_duplicate.xlsx",
        tag_row=1,
        description_row=2,
        units_row=3,
        data_start_row=4
    )

    if not success and message == "DUPLICATES_DETECTED":
        print(f"  [OK] SUCCESS: Duplicates detected correctly!")
        metadata = result
        print(f"    Duplicate count: {metadata.get('duplicate_count')}")
        print(f"    Existing range: {metadata.get('existing_date_range')}")
        print(f"    New range: {metadata.get('new_date_range')}")

        # Test 2b: Now confirm and proceed with the append
        print("\n[Test 2b] Confirming and proceeding with append...")
        success, message, df = dm.append_data_confirmed(
            metadata['new_filepath'],
            metadata['tag_row'],
            metadata['description_row'],
            metadata['units_row'],
            metadata['data_start_row'],
            metadata.get('skip_blank_columns', 0)
        )

        if success:
            print(f"  [OK] SUCCESS: {message}")
        else:
            print(f"  [FAIL] FAILED: {message}")
            return False
    else:
        print(f"  [FAIL] FAILED: Expected DUPLICATES_DETECTED, got success={success}, message={message}")
        return False

    # Test 3: Reset and load original data again
    print("\n[Test 3] Resetting and loading original data again...")
    dm.reset_session()
    success, message, df = dm.load_excel(
        "test_data.xlsx",
        tag_row=1,
        description_row=2,
        units_row=3,
        data_start_row=4
    )

    if success:
        print(f"  [OK] SUCCESS: Data reloaded")
    else:
        print(f"  [FAIL] FAILED: {message}")
        return False

    # Test 4: Append data WITHOUT duplicates (should proceed automatically)
    print("\n[Test 4] Appending data without duplicate timestamps...")
    success, message, df = dm.append_data(
        "test_data_append_no_duplicate.xlsx",
        tag_row=1,
        description_row=2,
        units_row=3,
        data_start_row=4
    )

    if success:
        print(f"  [OK] SUCCESS: {message}")
    elif message == "DUPLICATES_DETECTED":
        print(f"  [FAIL] FAILED: False positive - detected duplicates when there should be none")
        return False
    else:
        print(f"  [FAIL] FAILED: {message}")
        return False

    print("\n" + "=" * 60)
    print("All tests passed! [OK]")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_duplicate_detection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
