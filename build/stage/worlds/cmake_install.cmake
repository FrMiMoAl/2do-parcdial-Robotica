# Install script for directory: /home/franco/stage_ws/src/Stage/worlds

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/franco/stage_ws/install/stage")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "RELEASE")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/stage/worlds" TYPE FILE FILES
    "/home/franco/stage_ws/src/Stage/worlds/amcl-sonar.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/autolab.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/camera.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/everything.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/lsp_test.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/mbicp.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/nd.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/roomba.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/simple.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/test.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/uoa_robotics_lab.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/vfh.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/wavefront-remote.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/wavefront.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/wifi.cfg"
    "/home/franco/stage_ws/src/Stage/worlds/SFU.world"
    "/home/franco/stage_ws/src/Stage/worlds/autolab.world"
    "/home/franco/stage_ws/src/Stage/worlds/camera.world"
    "/home/franco/stage_ws/src/Stage/worlds/circuit.world"
    "/home/franco/stage_ws/src/Stage/worlds/everything.world"
    "/home/franco/stage_ws/src/Stage/worlds/fasr.world"
    "/home/franco/stage_ws/src/Stage/worlds/fasr2.world"
    "/home/franco/stage_ws/src/Stage/worlds/fasr_plan.world"
    "/home/franco/stage_ws/src/Stage/worlds/large.world"
    "/home/franco/stage_ws/src/Stage/worlds/lsp_test.world"
    "/home/franco/stage_ws/src/Stage/worlds/mbicp.world"
    "/home/franco/stage_ws/src/Stage/worlds/pioneer_flocking.world"
    "/home/franco/stage_ws/src/Stage/worlds/pioneer_follow.world"
    "/home/franco/stage_ws/src/Stage/worlds/pioneer_walle.world"
    "/home/franco/stage_ws/src/Stage/worlds/roomba.world"
    "/home/franco/stage_ws/src/Stage/worlds/sensor_noise_demo.world"
    "/home/franco/stage_ws/src/Stage/worlds/sensor_noise_module_demo.world"
    "/home/franco/stage_ws/src/Stage/worlds/simple.world"
    "/home/franco/stage_ws/src/Stage/worlds/uoa_robotics_lab.world"
    "/home/franco/stage_ws/src/Stage/worlds/wifi.world"
    "/home/franco/stage_ws/src/Stage/worlds/beacons.inc"
    "/home/franco/stage_ws/src/Stage/worlds/chatterbox.inc"
    "/home/franco/stage_ws/src/Stage/worlds/hokuyo.inc"
    "/home/franco/stage_ws/src/Stage/worlds/irobot.inc"
    "/home/franco/stage_ws/src/Stage/worlds/map.inc"
    "/home/franco/stage_ws/src/Stage/worlds/objects.inc"
    "/home/franco/stage_ws/src/Stage/worlds/pantilt.inc"
    "/home/franco/stage_ws/src/Stage/worlds/pioneer.inc"
    "/home/franco/stage_ws/src/Stage/worlds/sick.inc"
    "/home/franco/stage_ws/src/Stage/worlds/ubot.inc"
    "/home/franco/stage_ws/src/Stage/worlds/uoa_robotics_lab_models.inc"
    "/home/franco/stage_ws/src/Stage/worlds/walle.inc"
    "/home/franco/stage_ws/src/Stage/worlds/cfggen.sh"
    "/home/franco/stage_ws/src/Stage/worlds/test.sh"
    "/home/franco/stage_ws/src/Stage/worlds/worldgen.sh"
    )
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/home/franco/stage_ws/build/stage/worlds/benchmark/cmake_install.cmake")
  include("/home/franco/stage_ws/build/stage/worlds/bitmaps/cmake_install.cmake")
  include("/home/franco/stage_ws/build/stage/worlds/wifi/cmake_install.cmake")

endif()

