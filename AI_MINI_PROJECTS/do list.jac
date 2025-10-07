"""A Graph-Based To-Do List Manager"""

walker TaskManager {
    has task_text: str;
    has action: str;  # "add", "view", "complete"

    can start with `root entry;
    can handle_task with task entry;
}

node task {
    has text: str;
    has done: bool = False;
}

# CLI mode: simulate adding and viewing tasks
with entry:__main__ {
    root spawn TaskManager("Buy groceries", "add");
    root spawn TaskManager("Finish report", "add");
    root spawn TaskManager("", "view");
    root spawn TaskManager("Buy groceries", "complete");
    root spawn TaskManager("", "view");
}

impl TaskManager.start {
    if self.action == "add" {
        root ++> task(self.task_text);
        print(f"🆕 Added task: {self.task_text}");
        disengage;
    } elif self.action == "view" {
        visit [root --> (`?task)];
    } elif self.action == "complete" {
        visit [root --> (`?task)];
    }
}

impl TaskManager.handle_task {
    if self.action == "view" {
        status = "✅" if here.done else "🔲";
        print(f"{status} {here.text}");
        visit [-->];
    } elif self.action == "complete" and here.text == self.task_text {
        here.done = True;
        print(f"☑️ Completed task: {here.text}");
        disengage;
    } else {
        visit [-->];
    }
}