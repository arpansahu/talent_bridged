from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, AccountOrders, AccountOrdersHistory, Address


class AccountOrdersInline(admin.TabularInline):
    """
    Inline admin for AccountOrders.
    This allows managing orders directly from the Account admin page.
    """
    model = AccountOrders
    extra = 1  # Number of empty inline forms to display


class AccountAdmin(UserAdmin):
    """
    Custom admin for the Account model.
    """
    list_display = ('email', 'username', 'name', 'date_joined', 'last_login', 'is_admin', 'is_active')
    search_fields = ('email', 'username', 'name')
    readonly_fields = ('date_joined', 'last_login')

    list_filter = ('is_admin', 'is_active', 'is_staff')
    
    # Fieldsets for editing the account
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'name', 'password', 'profile_photo')
        }),
        ('Permissions', {
            'fields': ('is_admin', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Related Models', {
            'fields': ('address', 'api_key')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'name', 'password1', 'password2', 'profile_photo', 'is_admin', 'is_active', 'is_staff', 'is_superuser', 'address')}
         ),
    )

    ordering = ('email',)
    filter_horizontal = ()
    inlines = [AccountOrdersInline]  # Add inline for AccountOrders


class OrderHistoryInline(admin.TabularInline):
    """
    Inline admin for AccountOrdersHistory.
    This allows managing order history directly from the Order admin page.
    """
    model = AccountOrdersHistory
    extra = 1  # Number of empty inline forms to display for adding new order history entries
    readonly_fields = ('history_date',)  # Make history date read-only, since it’s auto-added

class AccountOrdersAdmin(admin.ModelAdmin):
    """
    Custom admin for the AccountOrders model.
    """
    list_display = ('account', 'order', 'start_date', 'end_date', 'is_active')
    search_fields = ('account__email', 'order__subscription_item__service_name')
    list_filter = ('is_active', 'order__subscription_item__subscription_type')
    readonly_fields = ('start_date',)

    inlines = [OrderHistoryInline]  # Add inline for AccountOrdersHistory



class AccountOrdersHistoryAdmin(admin.ModelAdmin):
    """
    Custom admin for AccountOrdersHistory.
    """
    list_display = ('account_order', 'change_type', 'history_date', 'details')
    search_fields = ('account_order__account__email', 'change_type')
    list_filter = ('change_type', 'history_date')
    readonly_fields = ('history_date',)



class AddressAdmin(admin.ModelAdmin):
    """
    Custom admin for Address model.
    """
    list_display = ('full_name', 'email', 'address1', 'city', 'state', 'zipcode', 'country')
    search_fields = ('full_name', 'email', 'city', 'zipcode')
    list_filter = ('city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(AccountOrders, AccountOrdersAdmin)
admin.site.register(AccountOrdersHistory, AccountOrdersHistoryAdmin)
admin.site.register(Address, AddressAdmin)
