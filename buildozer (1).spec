[app]

title = Песочница
package.name = sandboxstory
package.domain = org.example.sandbox
source.dir = .
source.include_exts = py,png,ttf
source.exclude_dirs = .github, bin, .buildozer, __pycache__
version = 1.0.0

requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.permissions =
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
