import sqlite3
import os

def format_table(headers, rows, max_rows=None):
    """Format data into a simple text table with optional row limit"""
    if not rows:
        return "No data available"
    
    # If max_rows is specified, add indicator of hidden rows
    display_rows = rows[:max_rows] if max_rows else rows
    total_rows = len(rows)
        
    # Calculate column widths
    widths = [len(str(header)) for header in headers]
    for row in display_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
            
    # Create separator line
    separator = '+' + '+'.join('-' * (width + 2) for width in widths) + '+'
    
    # Format headers
    header_str = '|' + '|'.join(f' {str(header):<{width}} ' 
                               for header, width in zip(headers, widths)) + '|'
    
    # Format rows
    row_strs = []
    for row in display_rows:
        row_str = '|' + '|'.join(f' {str(cell):<{width}} ' 
                                for cell, width in zip(row, widths)) + '|'
        row_strs.append(row_str)
    
    # Combine all parts
    table = '\n'.join([
        separator,
        header_str,
        separator,
        *row_strs,
        separator
    ])
    
    # Add indication of hidden rows if necessary
    if max_rows and total_rows > max_rows:
        table += f"\n... {total_rows - max_rows} more rows not shown ..."
    
    return table

def view_database(db_name='music_mood.db', rows_to_show=10):
    """View the contents of both tables in the database"""
    
    if not os.path.exists(db_name):
        print(f"Error: Database '{db_name}' not found!")
        return
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Check songs table
        print("\n=== Songs Table ===")
        cursor.execute("SELECT COUNT(*) FROM songs")
        total_songs = cursor.fetchone()[0]
        
        if total_songs == 0:
            print("Songs table is empty")
        else:
            cursor.execute("SELECT * FROM songs")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            print(format_table(columns, rows, rows_to_show))
            print(f"\nTotal songs: {total_songs}")
            
        # Check mood_analysis table
        print("\n=== Mood Analysis Table ===")
        cursor.execute("SELECT COUNT(*) FROM mood_analysis")
        total_moods = cursor.fetchone()[0]
        
        if total_moods == 0:
            print("Mood analysis table is empty")
        else:
            cursor.execute("SELECT * FROM mood_analysis")
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            print(format_table(columns, rows, rows_to_show))
            print(f"\nTotal mood analyses: {total_moods}")
            
    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    # You can adjust the number of rows to show
    view_database(rows_to_show=50)  # Show all 50 rows