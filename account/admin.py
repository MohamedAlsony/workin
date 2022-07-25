from django.contrib import admin
from account.models import Account,Profile

# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    list_display = ('email','firstname','lastname', 'is_company','date_joined', 'last_login', 'file',)
    search_fields = ('pk', 'email','firstname', 'lastname')
    readonly_fields=('pk', 'date_joined', 'last_login')

    filter_horizontal = ()
    list_filter = ('is_company',)
    fieldsets = ()


admin.site.register(Account, AccountAdmin)
admin.site.register(Profile)
