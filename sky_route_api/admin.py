from django.contrib import admin

from sky_route_api.models import (Airport, Route,
                                  Crew, Airplane,
                                  Flight, Order,
                                  Ticket, AirplaneType)

# Register your models here.
admin.site.register(AirplaneType)
admin.site.register(Airport)
admin.site.register(Route)
admin.site.register(Crew)
admin.site.register(Airplane)
admin.site.register(Flight)
admin.site.register(Order)
admin.site.register(Ticket)
