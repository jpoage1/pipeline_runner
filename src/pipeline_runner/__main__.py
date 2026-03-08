if __name__ == "__main__":
    from pipeline_runner.tasks.example_tasks import ExampleTask
    from pipeline_runner.core.pipeline_runner import runner

    runner(tasks=[ExampleTask])
