# 📦 Task Master Pro

A powerful and intuitive Task Management Dashboard built with Python and Streamlit. This application combines a calendar-based workflow with "Sprint" style analytics to help you manage deadlines, daily habits, and long-term resolutions efficiently.

## ✨ Features

### 📅 Calendar Dashboard
* **Visual Deadline Management:** View all tasks on an interactive calendar.
* **Sprint Logic:** Tasks are automatically grouped into "Packages" or "Sprints" based on end dates. You cannot create a new package until the current one is finished or expired.
* **Daily Checklists:** Create tasks with daily sub-items (checkboxes) that auto-update the parent task's progress.
* **Task Locking:** Expired tasks are automatically locked to prevent historical editing.
* **Sidebar Quick Access:** Manage resolutions and update active task progress directly from the sidebar without navigating away.

### 📈 Analytics & Resolutions
* **Sprint Efficiency:** View your performance over the last 7 sprints.
* **Current Status Pie Chart:** Quick visualization of completed vs. pending tasks in the current cycle.
* **Sprint History:** Expandable list of all past sprints with detailed task breakdowns.
* **New Year Resolutions:** A dedicated section to lock in long-term goals (editable only until Jan 3rd).

## 🚀 Installation & Run

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/task-master-pro.git](https://github.com/yourusername/task-master-pro.git)
    cd task-master-pro
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

## 📂 Project Structure

* `app.py`: The main executable file handling the UI and page logic.
* `database.py`: Backend module managing SQLite database connections and logic.
* `task_tracker_v3.db`: SQLite database file (auto-generated on first run).
* `requirements.txt`: List of Python dependencies.

## 🛠️ Built With
* [Streamlit](https://streamlit.io/)
* [Pandas](https://pandas.pydata.org/)
* [Plotly](https://plotly.com/)
* [Streamlit Calendar](https://pypi.org/project/streamlit-calendar/)
* SQLite3
