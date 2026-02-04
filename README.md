# MASCAR
Assets and codebase for the Multi-Agent Synchronized Collaborative Assembly Replication (MASCAR) testbed.  This testbed was developed by the Collaborative Robotics Lab at the National Institute of Standards and Technology.

# Overview Video
View here:  https://youtu.be/IEJgwW6c2EQ

[![MASCAR intro video](/MASCAR_video_thumbnail.png)](http://www.youtube.com/watch?v=IEJgwW6c2EQ "Introduction to MASCAR")

# Documentation
Please see our short paper in HRI 2026 for an overview:

[Local version](/HRI_2026_LBR%20-%20MASCAR.pdf)

[ACM Digital Library]() - Forthcoming

# Table of Contents
[CAD Files](/CAD%20Files/)
- [Testbed Components](/CAD%20Files/Testbed%20Components/)
    - [Cart and Tabletop](/CAD%20Files/Testbed%20Components/Cart%20and%20Tabletop/) - 
    Contains 2D and 3D models for recreation of the elements of the testbed, including the cart, surface mounting plates, and optical table tabletop design.
    - [Gripper Components](/CAD%20Files/Testbed%20Components/Gripper%20Components/) - Designs for yoke flange attached to the Robotiq 2F-85 for manual positioning and button control
    - [MoCap Marker Plates](/CAD%20Files/Testbed%20Components/MoCap%20Marker%20Plates/) - Models for attaching reflective mocap markers to the camera cold shoe mounts
    - [Raspberry Pi](/CAD%20Files/Testbed%20Components/Raspberry%20Pi/) - RP case models
    - 'NIST - Espressif ESP32-C3-DevKitC Case.stl' - Custom-designed case for ESP32
    - 'Laser_Diode_Holder.step' - 

[Design Documentation](/Design%20Documentation/)
- Diagrams, Bill of Materials, process description, design notes, and other instructions for running components of the testbed

[Safety](/Safety/)
- [Human Subjects Testbed](/Safety/Human%20Subjects%20Testbed/) - SOP for testbed setup & assembly
- [Universal Robots](/Safety/Universal%20Robots/) - Safety Manual for use of the UR3e

[Source Code](/Source%20Code/)
- [Python Code](/Source%20Code/Python%20Code/)) - Contains the code for controlling the Robotiq gripper via Raspberry Pi and UR RTDE, and the logger code for recording robot & gripper states
- [URCaps](/Source%20Code/URCaps/) - URCap program to be installed on UR3 for custom Robotiq gripper control

