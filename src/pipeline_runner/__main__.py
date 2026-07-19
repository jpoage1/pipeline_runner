"""Entry point for running the pipeline runner as a module."""

if __name__ == "__main__":
    from pipeline_runner.core.pipeline_runner import runner
    from pipeline_runner.tasks.example_tasks import ExampleTask

    runner(tasks=[ExampleTask])
