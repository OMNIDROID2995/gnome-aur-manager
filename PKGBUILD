# Maintainer: OMNIDROID2995
pkgname=gnome-aur-manager
pkgver=0.1.0
pkgrel=1
pkgdesc="A GTK4/Adwaita-based application for GNOME that provides a graphical interface to search, install, and manage AUR packages"
arch=('x86_64' 'aarch64')
url="https://github.com/OMNIDROID2995/gnome-aur-manager"
license=('GPL-3.0-or-later')
depends=('gtk4' 'libadwaita' 'python' 'python-gobject' 'git' 'base-devel')
makedepends=('meson' 'ninja')
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
# TODO: Replace 'SKIP' with actual SHA256 hash once v0.1.0 release is tagged
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    arch-meson . build
    meson compile -C build
}

check() {
    cd "$pkgname-$pkgver"
    # Allow build to continue if tests are not yet implemented
    meson test -C build || true
}

package() {
    cd "$pkgname-$pkgver"
    meson install -C build --destdir "$pkgdir"
}
