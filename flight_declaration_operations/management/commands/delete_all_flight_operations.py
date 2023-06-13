from django.core.management.base import BaseCommand, CommandError
from flight_declaration_operations.models import FlightDeclaration

class Command(BaseCommand):
    help = 'This command delete.'

    def add_arguments(self, parser):

        parser.add_argument(
        "-d",
        "--dry_run",
        dest = "dry_run",
        metavar = "Set if this is a dry run",
        default= '1', 
        help='Set if it is a dry run')
        


    def handle(self, *args, **options):
        
        dry_run = options['dry_run']                 
        dry_run = 1 if dry_run =='1' else 0

        all_operations = FlightDeclaration.objects.all()
        for a in all_operations:
            if dry_run: 
                print("Dry Run : Deleting operation %s"% a.id)
            else:
                print("Deleting operation %s..."% a.id)
                a.delete()
