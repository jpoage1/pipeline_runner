if __name__ == "__main__":
    from tasks.example_tasks import ExampleTask
    from core.pipeline_runner import runner

    runner(tasks=[ExampleTask])
