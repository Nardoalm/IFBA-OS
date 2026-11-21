cmake_minimum_required(VERSION 3.22)
project(ifba_app_description_runner LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(ECM REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${ECM_MODULE_PATH})
include(GNUInstallDirs)
find_package(Qt6 REQUIRED COMPONENTS Core)
set(KDE_INSTALL_BINDIR "${CMAKE_INSTALL_BINDIR}")
set(KDE_INSTALL_SBINDIR "${CMAKE_INSTALL_SBINDIR}")
set(KDE_INSTALL_LIBDIR "${CMAKE_INSTALL_LIBDIR}")
set(KDE_INSTALL_LIBEXECDIR "${CMAKE_INSTALL_LIBEXECDIR}")
set(KDE_INSTALL_DATADIR "${CMAKE_INSTALL_DATADIR}")
set(KDE_INSTALL_SYSCONFDIR "${CMAKE_INSTALL_SYSCONFDIR}")
set(KDE_INSTALL_INCLUDEDIR "${CMAKE_INSTALL_INCLUDEDIR}")
set(KDE_INSTALL_LOCALSTATEDIR "${CMAKE_INSTALL_LOCALSTATEDIR}")
set(KDE_INSTALL_SHAREDSTATEDIR "${CMAKE_INSTALL_SHAREDSTATEDIR}")
set(KDE_INSTALL_DATAROOTDIR "${CMAKE_INSTALL_DATAROOTDIR}")
set(KDE_INSTALL_LOCALEDIR "${CMAKE_INSTALL_LOCALEDIR}")
set(KDE_INSTALL_MANDIR "${CMAKE_INSTALL_MANDIR}")
set(KDE_INSTALL_INFODIR "${CMAKE_INSTALL_INFODIR}")
include(KDEInstallDirs6)
include(KDECMakeSettings)
include(KDECompilerSettings NO_POLICY_SCOPE)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

find_package(KF6CoreAddons REQUIRED)
find_package(KF6I18n REQUIRED)
find_package(KF6KIO REQUIRED)
find_package(KF6Runner REQUIRED)
find_package(KF6Service REQUIRED)
find_package(KF6JobWidgets REQUIRED)

kcoreaddons_add_plugin(ifba_app_description_runner
    SOURCES appdescriptionrunner.cpp appdescriptionrunner.h descriptionmatcher.h
    INSTALL_NAMESPACE "kf6/krunner"
)

target_link_libraries(ifba_app_description_runner PRIVATE
    KF6::CoreAddons
    KF6::I18n
    KF6::JobWidgets
    KF6::KIOGui
    KF6::Runner
    KF6::Service
)

include(CTest)
if(BUILD_TESTING)
    find_package(Qt6 REQUIRED COMPONENTS Test)
    add_executable(tst_description_matcher tests/DescriptionMatcherTest.cpp)
    target_link_libraries(tst_description_matcher PRIVATE Qt6::Core Qt6::Test)
    add_test(NAME description-matcher COMMAND tst_description_matcher)
endif()
