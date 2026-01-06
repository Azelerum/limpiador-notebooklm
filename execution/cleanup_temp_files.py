import os
import time

def cleanup_old_files(directory, max_age_seconds=3600):
    """
    Deletes files in the specified directory older than max_age_seconds.
    """
    now = time.time()
    count = 0
    if not os.path.exists(directory):
        return 0
        
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if os.stat(filepath).st_mtime < now - max_age_seconds:
                os.remove(filepath)
                count += 1
    return count

if __name__ == "__main__":
    # Example cleanup for the .tmp subdirectories
    tmp_path = os.path.join(os.getcwd(), ".tmp")
    for sub in ["uploads", "processed"]:
        path = os.path.join(tmp_path, sub)
        removed = cleanup_old_files(path)
        if removed > 0:
            print(f"Cleaned up {removed} files from {sub}")
