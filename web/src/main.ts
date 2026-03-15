const path = window.location.pathname || '/'
if (path.startsWith('/admin')) {
  void import('./main_admin')
} else {
  void import('./main_app')
}
