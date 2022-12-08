# Gramps - a GTK+/GNOME based genealogy program
# Nov 2022
# File: displayExiv2.gpr.py - a 'Gramps Plugin Registration' Python file  
# using Gramps built-in the GExiv2 interface
register(
    GRAMPLET,
    id = "Display Exiv2 Data", 
    name = _("Display Exiv2 Data"),
    description = _("Gramplet to display Exiv2 image metadata"),
    authors = ["Arnold Wiegert"],
    authors_email = ["http://gramps-project.org"],
    status = STABLE,
    version = "0.0.2",
    fname = "displayExiv2.py",
    height = 20,
	expand = True,
    detached_width = 400,
    detached_height = 500,
    gramplet = 'DisplayExiv2',
    navtypes = ['Media'],
    gramplet_title = _("Display Exiv2 metadata"),
    gramps_target_version = "5.1",
    help_url = "Addon:Display Exiv2 metadata",
    include_in_listing = True,
    )
