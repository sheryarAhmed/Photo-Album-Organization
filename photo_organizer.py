
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from sklearn.cluster import KMeans
import numpy as np
import os
import shutil
import cv2
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from PIL import Image, ImageTk

class PhotoAlbumOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Album Organizer")
        self.root.geometry("400x350")
        self.root.configure(bg="black")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='black', foreground='white')
        style.configure('TButton', background='blue', foreground='white')
        style.configure('TLabel', font=('Arial', 16))
        style.configure('Horizontal.TProgressbar', background='blue', troughcolor='black')

        self.upload_button = ttk.Button(self.root, text="Upload Folder", command=self.upload_folder)
        self.upload_button.pack(pady=20)

        self.progress_label = ttk.Label(self.root, text="Progress: 0%", foreground="white", background="black")
        self.progress_label.pack()

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate", style='Horizontal.TProgressbar')
        self.progress_bar.pack(pady=10)

        self.progress_files = ttk.Label(self.root, text=" ", foreground="white", background="black")
        self.progress_files.pack()

        self.cluster_label = ttk.Label(self.root, text="Select Number of Clusters:")
        self.cluster_label.pack()

        self.cluster_options = tk.StringVar(self.root)
        self.cluster_options.set("2")
        self.cluster_menu = ttk.Combobox(self.root, textvariable=self.cluster_options, values=["1", "2", "3", "4"])
        self.cluster_menu.pack(pady=10)

        self.result_button = ttk.Button(self.root, text="Start Data Processing", command=self.show_result)
        self.result_button.pack(pady=20)

        self.X_test = None
        self.X_filenames = None

    def upload_folder(self):
        self.folder_path = filedialog.askdirectory()
        self.X_test, self.X_filenames = self.images_resize(self.folder_path, TARGET)
        # self.update_progress(0)

    def update_progress(self, value):
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"Progress: {value}%")
        # if value < 100:
        #     self.root.after(100, self.update_progress, value + 1)

    def show_result(self):
        try:
            
            num_clusters = int(self.cluster_options.get())

            kmeans, labels = self.k_means(self.X_test, num_clusters)
            clustered_images, clustered_filenames = self.cluster_extraction(kmeans, labels)
            self.move_images(self.folder_path, clustered_filenames, kmeans)
            result_window = tk.Toplevel(self.root)
            result_window.title("Data Processing Results")
            result_window.geometry("300x150")

            results_label = ttk.Label(result_window, text=f"Clusters: {labels}", font=('Arial', 16))
            results_label.pack(pady=10)

            result_button = ttk.Button(result_window, text="Show Results", command=lambda: self.show_results(kmeans, clustered_images))
            result_button.pack(pady=10)

            self.visualization(self.X_test, labels)
            

        except Exception as e:
            print(f"Error: {str(e)}")

    def images_resize(self, folder_name, target):
        X_test = []
        X_filenames = []
        i = 0
        total_files = len(os.listdir(folder_name))
        for filename in os.listdir(folder_name):
            try:
                img = cv2.imread(os.path.join(folder_name, filename))
                img = cv2.resize(img, target)  # Resize to ensure consistent shape
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                flattened = img.flatten()
            except:
                print(f"Error in file {filename} ")
                break

            X_test.append(flattened)
            X_filenames.append(filename)
            i += 1
            print(f"file:{filename} Completed:{int((i/total_files)*100)} %")
            self.update_progress(int((i/total_files)*100))
            self.progress_files.config(text=f"Files:  {filename}")
            root.update()
        return np.array(X_test), np.array(X_filenames)

    def cluster_extraction(self, kmeans, labels):
        clustered_images = [[] for _ in range(kmeans.n_clusters)]  # Lists for each cluster
        clustered_filenames = [[] for _ in range(kmeans.n_clusters)]
        for i, label in enumerate(labels):
            clustered_images[label].append(self.X_test[i])  # Reshape to the original image format
            clustered_filenames[label].append(self.X_filenames[i])  # Reshape to the original image format
        return clustered_images, clustered_filenames

    def k_means(self, images, cluster):
        kmeans = KMeans(n_clusters=cluster, n_init=10)
        labels = kmeans.fit_predict(images)
        return kmeans, labels

    def show_results(self, kmeans, clustered_images):
        result_window = tk.Toplevel(self.root)
        result_window.title("Clustered Results")

        for i in range(kmeans.n_clusters):
            cluster_frame = ttk.Frame(result_window,relief='solid', borderwidth=5)
            cluster_frame.pack(pady=10)

            ttk.Label(cluster_frame, text=f"Cluster {i}", font=('Arial', 14),foreground="blue").pack()

            for j in range(min(3, len(clustered_images[i]))):
                image_label = ttk.Label(cluster_frame, text=f"Image {j}")
                image_label.pack(side="left",padx=10)

                img = clustered_images[i][j].reshape(100, 100, 3)
                # img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                img = cv2.resize(img, (200, 200))
                img = Image.fromarray(img)
                img = ImageTk.PhotoImage(img)

                panel = ttk.Label(cluster_frame, image=img,border=10, relief="solid")
                panel.image = img
                panel.pack(side="left",padx=10)

        result_window.mainloop()

    def visualization(self, X_test, labels):
        pca = PCA(n_components=2)  # Reduce to 2D for visualization
        reduced_features = pca.fit_transform(X_test)
        plt.scatter(reduced_features[:, 0], reduced_features[:, 1], c=labels)
        plt.title("Cluster Visualization using PCA")
        plt.show()

    def move_images(self, folder, clustered_filenames, kmeans):
        upload_dir = folder
        labels_dir = "labels"

        # Create label folders if they don't exist
        for label in range(kmeans.n_clusters):
            label_dir = os.path.join(labels_dir, f"label_{label}")
            os.makedirs(label_dir, exist_ok=True)  # Create only if it doesn't exist

        # Move images to corresponding label folders
        for label, filenames in enumerate(clustered_filenames):
            for filename in filenames:
                source_path = os.path.join(upload_dir, filename)
                dest_path = os.path.join(labels_dir, f"label_{label}", filename)
                shutil.copy2(source_path, dest_path)


if __name__ == "__main__":
    TARGET = (100, 100)  # Assuming this is a global variable

    root = tk.Tk()
    app = PhotoAlbumOrganizer(root)
    root.mainloop()




