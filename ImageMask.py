# =========================================================================================================================================
# Breif:    This code opens allows the user to load an image, preferably .PNG at 1000*1000 and them indicate features.
#           The circles to highlight the stomata and trichomes should be used first, as the brush for viens obscures much of the image.
#           Pressing 'calculate' opens a popup table that displays the count and percentage cover imformation, paired with knowledge of
#           of the feild of view, this can be used to indicate total vein coverage and counts for the leaf sample. 
# Input:    Image file, ideally 1000*1000 px .PNG
# Output:   .CSV file with calculated information
# Author:   Evan Kear
# Date:     22/09/2024        
# =========================================================================================================================================




# =========================================================================================================================================
# Section: Imports Statements and Global Variables
# =========================================================================================================================================

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import csv
import os

# Global variables
selected_mask = 'circle_1'  # Default to the stomata mask (first button)
brush_size = 10  # Brush size - controlled by slider
circle_radius_1 = 40  # Circle 1 radius
circle_radius_2 = 40  # Circle 2 radius
red_threshold = 200  # Threshold to detect red pixels (for 'brush'), doesnt matter much as images will be B&W
tree = None # Set values for tree for the checks later on 
measurement_table = [["Image ID", "Stomata Count", "Trichome Count", "Vein Coverage"],] # Create a table for measurments 
stomata_mask_positions = [] # Lists to store circle positions
trichome_mask_positions = [] # Lists to store circle positions


# =========================================================================================================================================
# Section: Masking and Drawing Functions
# =========================================================================================================================================

# Function to select an image from files (called by a button press in the control_window)
def open_image():
    global image, draw_canvas, canvas, image_name, stomata_mask_positions, trichome_mask_positions
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp")])
    
    if file_path:
        # Load image using PIL
        image = Image.open(file_path)
        image = image.convert("RGB")
        draw_canvas = ImageDraw.Draw(image)  # Initialize drawing canvas
        
        # Update the canvas to display the image
        update_image()
        print(f"Image loaded: {file_path}")

        # Update the global image_name
        image_name = os.path.basename(file_path)

    # Reset these values upon loading a new image
    stomata_mask_positions = []
    trichome_mask_positions = []

# Function to switch to brush mode for drawing viens (called by a button press in the control_window)
def select_brush_mask():
    global selected_mask
    selected_mask = 'brush'
    print("Switched to Brush Mask")

# Function to switch to circle 1 mode for stomata DEFAULT (called by a button press in the control_window)
def select_stomata_mask():
    global selected_mask
    selected_mask = 'circle_1'
    print("Switched to Stomata Mask 1")

# Function to switch to circle 2 mode for trichomes (called by a button press in the control_window)
def select_trichome_mask():
    global selected_mask
    selected_mask = 'circle_2'
    print("Switched to Trichome Mask 2")

# Function for drawing with a brush on the mask 
def draw(event):
    global draw_image, selected_mask, brush_size

    if not image:  # Stops the drawing if no image exists
        return

    x, y = event.x, event.y  # Get mouse position

    if selected_mask == 'brush':
        # Draw with brush (circle) on the image at every drag
        # This update happens a little slow, so you can see the circles rather than a true brush
        # Will add ability to change the brush size
        draw_canvas.ellipse((x - brush_size, y - brush_size, x + brush_size, y + brush_size), fill='red', outline='red')

    update_image()  # Update the canvas with the new drawing

# Function to draw a circle after mouse click
def place_circle(event):
    global draw_image, selected_mask, circle_radius_1, circle_radius_2

    if not image:  # Stops the drawing if no image exists
        return

    x, y = event.x, event.y  # Get mouse position

    if selected_mask == 'circle_1':
        # Draw Circle Mask 1 (green) on a single click and store position
        draw_canvas.ellipse((x - circle_radius_1, y - circle_radius_1, x + circle_radius_1, y + circle_radius_1),
                            outline='green', width=3)
        stomata_mask_positions.append((x, y))  # Store circle position, 
        # this could be a simple counter, but using positions stops two circles being drawn on top of each other??

    elif selected_mask == 'circle_2':
        # Draw Circle Mask 2 (blue) on a single click and store position
        draw_canvas.ellipse((x - circle_radius_2, y - circle_radius_2, x + circle_radius_2, y + circle_radius_2),
                            outline='blue', width=3)
        trichome_mask_positions.append((x, y))  # Store circle position

    update_image()  # Update the canvas with the new drawing

# Function to update the canvas with the image
def update_image():
    if image:
        tk_image = ImageTk.PhotoImage(image=image)
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        canvas.image = tk_image  # Keep reference to avoid garbage collection


# =========================================================================================================================================
# Section: Calculations and CSV creation
# =========================================================================================================================================

# Function to calculate the brush-covered area and the number of circles (called by a button press in the control_window)
def calculate_results():
    global measurement_table, image_name
    if not image:  # Stops calculation if no image exists
        messagebox.showwarning("Warning", "No image loaded.")
        return

    # Convert image to array for pixel data
    image_np = np.array(image)

    # Calculate red pixels (for 'brush' mask)
    red_pixels = (image_np[:, :, 0] > red_threshold) & (image_np[:, :, 1] < 50) & (image_np[:, :, 2] < 50)
    total_pixels = image_np.shape[0] * image_np.shape[1]
    brush_area_percentage = ((np.sum(red_pixels)) / total_pixels) * 100
    brush_area_percentage = round(brush_area_percentage, 2)

    # Count the number of circles (by counting the entries in the position lists)
    num_green_circles = len(stomata_mask_positions)  # Circle Mask 1 - Stomata (green)
    num_blue_circles = len(trichome_mask_positions)  # Circle Mask 2 - Trichome (blue)
    
    # Create list with the new results
    measurements = [image_name, num_green_circles, num_blue_circles, brush_area_percentage]
    print(measurements)

    # Update global measurement_list
    measurement_table.append(measurements)
    print(measurement_table)

    #open the table window after calculation 
    open_table_window()

# Function to export the table data to a .CSV file
def export_to_csv(tree):
    # Open file dialog to choose the file name and location
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    
    if file:
        # Get the data from the treeview
        rows = [(tree.item(row)["values"]) for row in tree.get_children()]
        
        # Write the data to a CSV file
        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            # Write the header
            writer.writerow(["Mask Type", "Area (%)", "Count", "Density"])
            # Write the data rows
            writer.writerows(rows)
        print(f"Data exported to {file}")


# =========================================================================================================================================
# Section: Creating Main Window and the Control Window
# =========================================================================================================================================

# Initialize tkinter main window
root = tk.Tk()
root.title("Image Masking Tool")

# Create a tkinter Canvas widget to display the image
canvas = tk.Canvas(root, width=1000, height=1000)  # Initial size, doesn't reseize, I should force a window size, or an image size
canvas.pack()

# Setup a second window for control buttons
control_window = tk.Toplevel(root)  # Create a window for the controls
control_window.attributes("-topmost", True) # places the window above all others
control_window.geometry("200x300")
control_window.title("Controls")

# Create buttons for control options
open_image_button = tk.Button(control_window, text="Open Image", command=open_image)
open_image_button.pack(pady=5)

circle_button_1 = tk.Button(control_window, text="Stomata", command=select_stomata_mask)
circle_button_1.pack(pady=5)

circle_button_2 = tk.Button(control_window, text="Trichome", command=select_trichome_mask)
circle_button_2.pack(pady=5)

brush_button = tk.Button(control_window, text="Vein Brush", command=select_brush_mask)
brush_button.pack(pady=5)

# Function to update the brush size using the value of the slider
def update_value(val):
    global brush_size
    brush_size = int(val)

# Create a slider to control the brush size
brush_slider = tk.Scale(control_window, from_=0, to=100, orient=tk.HORIZONTAL, command=update_value)
brush_slider.pack(pady=5)
brush_slider.set(brush_size)

# Button to calculate the results
calculate_button = tk.Button(control_window, text="Calculate", command=calculate_results)
calculate_button.pack(side=tk.TOP, pady=5)


# =========================================================================================================================================
# Section: Creating the Table Window
# =========================================================================================================================================

# Function to check for measurment table window
def open_table_window():
    global tree
    if tree is None:
        # Create a new window for the table
        table_window = tk.Toplevel(root)
        table_window.title("Measurements Table")
        
        # Create a treeview widget for displaying the table
        tree = ttk.Treeview(table_window, show='headings')
        tree["columns"] = measurement_table[0]
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add an export button
        export_button = tk.Button(table_window, text="Export to CSV", command=lambda: export_to_csv(tree))
        export_button.pack(pady=10)

        update_table()

    else:

        update_table()

# Function to update the table_window with values from measurement_table
def update_table():
    global measurement_table, tree
    # Clear table
    for item in tree.get_children():
        tree.delete(item)

    # Add the measurements to the table
    for col in measurement_table[0]:
        tree.heading(col, text=col)  # Set column headers
        tree.column(col, width=100)  # Set column width
    for row in measurement_table[1:]:
        tree.insert("", "end", values=row)


# =========================================================================================================================================
# Section: Binding Mouse Events and Starting tkinter
# =========================================================================================================================================

# Bind mouse events for drawing and placing circles
canvas.bind("<B1-Motion>", draw)  # Brush draws when mouse dragged
canvas.bind("<Button-1>", place_circle)  # Circle when mouse clicks

# Run the tkinter main loop
root.mainloop()
