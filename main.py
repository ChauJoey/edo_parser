from workflow.workflow_manager import WorkflowManager

def main():
    workflow = WorkflowManager(source="input", verbose=True)
    workflow.run()

if __name__ == "__main__":
    main()
