"""A Simple To-Do List Manager"""

class TaskManager {
    def init(self: TaskManager) {
        self.tasks = [];
    }

    def show_tasks(self: TaskManager) {
        if len(self.tasks) == 0 {
            print("✅ Your to-do list is empty!");
        } else {
            print("🗂️ Your To-Do List:");
            for i in range(len(self.tasks)) {
                print(f"{i + 1}. {self.tasks[i]}");
            }
        }
    }

    def add_task(self: TaskManager) {
        task = input("Enter a new task: ");
        self.tasks.append(task);
        print("🆕 Task added!");
    }

    def remove_task(self: TaskManager) {
        self.show_tasks();
        index_str = input("Enter the number of the task to remove: ");
        if index_str.isdigit() {
            index = int(index_str) - 1;
            if index >= 0 and index < len(self.tasks) {
                removed = self.tasks.pop(index);
                print(f"🗑️ Removed: {removed}");
            } else {
                print("❌ Invalid task number.");
            }
        } else {
            print("❌ Please enter a valid number.");
        }
    }

    def menu(self: TaskManager) {
        while True {
            print("\n📋 To-Do List Menu:");
            print("1. View tasks");
            print("2. Add task");
            print("3. Remove task");
            print("4. Exit");
            choice = input("Choose an option: ");

            if choice == "1" {
                self.show_tasks();
            } elif choice == "2" {
                self.add_task();
            } elif choice == "3" {
                self.remove_task();
            } elif choice == "4" {
                print("👋 Goodbye!");
                break;
            } else {
                print("❌ Invalid choice. Try again.");
            }
        }
    }
}

with entry {
    manager = TaskManager();
    manager.menu();
}
