def register_routes(app):
    from .auth import (
        login,
        register,
        logout,
        forgot_password,
        verify_code,
        reset_password,
    )
    from .main import (
        landing_apresentacao,
        welcome,
        index,
    )
    from .logs import (
        logs_page,
        api_logs,
        api_logs_sensors,
        api_logs_export,
        api_logs_export_pdf,
    )
    from .admin import (
        admin_panel,
        admin_approve,
        admin_reject,
        admin_revoke,
        admin_change_role,
        admin_bind_rover,
    )
    from .profile import (
        settings_page,
        api_profile,
        api_change_password,
        api_rover_status,
        api_rover_link,
        api_rover_unlink,
    )
    from . import rover

    app.add_url_rule('/', endpoint='landing_apresentacao', view_func=landing_apresentacao)
    app.add_url_rule('/app', endpoint='welcome', view_func=welcome)
    app.add_url_rule('/dashboard', endpoint='index', view_func=index)

    app.add_url_rule('/login', endpoint='login', view_func=login, methods=['GET', 'POST'])
    app.add_url_rule('/register', endpoint='register', view_func=register, methods=['GET', 'POST'])
    app.add_url_rule('/logout', endpoint='logout', view_func=logout)
    app.add_url_rule('/forgot-password', endpoint='forgot_password', view_func=forgot_password, methods=['GET', 'POST'])
    app.add_url_rule('/verify-code', endpoint='verify_code', view_func=verify_code, methods=['POST'])
    app.add_url_rule('/reset-password', endpoint='reset_password', view_func=reset_password, methods=['GET', 'POST'])

    app.add_url_rule('/logs', endpoint='logs_page', view_func=logs_page)
    app.add_url_rule('/api/logs', endpoint='api_logs', view_func=api_logs)
    app.add_url_rule('/api/logs/sensors', endpoint='api_logs_sensors', view_func=api_logs_sensors)
    app.add_url_rule('/api/logs/export', endpoint='api_logs_export', view_func=api_logs_export)
    app.add_url_rule('/api/logs/export/pdf', endpoint='api_logs_export_pdf', view_func=api_logs_export_pdf)

    app.add_url_rule('/admin', endpoint='admin_panel', view_func=admin_panel)
    app.add_url_rule('/admin/approve', endpoint='admin_approve', view_func=admin_approve, methods=['POST'])
    app.add_url_rule('/admin/reject', endpoint='admin_reject', view_func=admin_reject, methods=['POST'])
    app.add_url_rule('/admin/revoke', endpoint='admin_revoke', view_func=admin_revoke, methods=['POST'])
    app.add_url_rule('/admin/change-role', endpoint='admin_change_role', view_func=admin_change_role, methods=['POST'])
    app.add_url_rule('/admin/bind-rover', endpoint='admin_bind_rover', view_func=admin_bind_rover, methods=['POST'])

    app.add_url_rule('/settings', endpoint='settings_page', view_func=settings_page)
    app.add_url_rule('/api/profile', endpoint='api_profile', view_func=api_profile, methods=['POST'])
    app.add_url_rule('/api/change-password', endpoint='api_change_password', view_func=api_change_password, methods=['POST'])
    app.add_url_rule('/api/rover/status', endpoint='api_rover_status', view_func=api_rover_status)
    app.add_url_rule('/api/rover/link', endpoint='api_rover_link', view_func=api_rover_link, methods=['POST'])
    app.add_url_rule('/api/rover/unlink', endpoint='api_rover_unlink', view_func=api_rover_unlink, methods=['POST'])