from django_extensions.management.jobs import BaseJob, MinutelyJob 

class Job(MinutelyJob):
    help = "Test Job"
    def execute(self):
        print("Hello World")
        