
=============
Hillmaker FAQ
=============

Introduction
------------

  Q. What is hillmaker?

  A. Hillmaker is a Python package that can be used to create statistical and graphical summaries of
arrival, departure and occupancy patterns by time of day for systems having entities flowing into and out
of some location or state.

  Hillmaker includes the following main components:

    * an MS Access form based add-in that calculates the various statistics and stores them in Access tables,

    * an MS Excel based spreadsheet that can be used to create graphs from Hillmaker output.


  Q. Who would use such a tool?

  A. Hillmaker was developed in response to many practical analysis problems arising in health care delivery
     systems such as hospitals and outpatient clinics. It has been used by operations analysts, management
     engineers and other such analytical folk. A journal publication describing its use
     in this environment is:

     Isken, M.W. (2002) �Modeling and Analysis of Occupancy Data: A Healthcare Capacity Planning Application,�
     International Journal of Information Technology and Decision Making, 1, 4 (December) 707-729.


  Q. Who develops and maintains Hillmaker?

  A. Hillmaker is currently developed and maintained by Mark Isken,
  Department of Decision and Information Sciences, Oakland University, Rochester, MI, USA.
  E-mail: <isken@oakland.edu>.


  Q. How is Hillmaker licensed?

  A. Hillmaker is currently licensed under the GNU General Public License
  (GPL). GLPK is free software; you can redistribute it and/or modify it
  under the terms of the GNU General Public License as published by the
  Free Software Foundation; either version 2, or (at your option) any
  later version.


  Q. Where is the Hillmaker home page?

  http://hillmaker.sourceforge.net


  Q. Why was Hillmaker developed in MS Access?

  A. This is simply a result of its history. It started out as a DOS Basic application many years ago, was ported to
     FoxPro, and then to MS Access when it became available.

  Q. Are there plans to port it to an open source database and spreadsheet platform?

  A. Yes. Would you like to help?

  Q. How do I download and install Hillmaker?

     See InstallAndQuickStart.doc.


  Q. Is there a Hillmaker mailing list or newsgroup?

  A. For now, just the default Forums are available on the SourceForge site.


  Q. Who maintains this FAQ and how do I contribute to this FAQ?

  A. The present maintainer of this FAQ is Mark Isken (isken@oakland.edu).

  All contributions to this FAQ, such as questions and (preferably)
  answers should be sent to the <isken@oakland.edu> email address.
  This FAQ is copyright Mark Isken 2005 and is released under the
  same license, terms and conditions as Hillmaker, that is, GPL version 2 or
  later.

  Contributions are not directly referenced in the body of the FAQ as
  this would become unmanageable and messy, but rather as a list of
  contributors to this FAQ. If you are the author of any information
  included in this FAQ and you do not want your content to be included,
  please contact the FAQ maintainer and your material will be removed.
  Also if you have not been correctly included as a contributor to this
  FAQ, your details have changed, or you do not want your name listed in
  the list of contributors, please contact the FAQ maintainer for
  correction.


  Q. Where can I download this FAQ?

  http://hillmaker.sourceforge.net/hillmaker-faq.txt


  Q. Who are the FAQ contributors?

  A. The FAQ contents were created from the following sources:

    * Mark Isken


Hillmaker functions & features

  Q. What is the current state of Hillmaker development?

  A. Version 0.8 is the current version and it works. There are a number of issues however that
     require work:

  * No online help exists
  * A good install procedure is needed to cope with the fact that different versions of MS Office
    use different object libraries. This might be especially problematic for things like the chart control,
    calendar control and file dialog controls.
  * The graphing spreadsheets need some enhancements (e.g. stacked bar percentiles not implemented, capacity
    line not implemented)


  Q. Why not use a statistics package instead of Hillmaker?

  A. You certainly could, though I imagine you'd end up writing scripts that mimic Hillmaker's logic.
     If you're a wizard with some stat package then run Hillmaker and duplicate its outputs in your
     favorite stat package and then tell us all how you did it. :)


  Q. What input file formats does Hillmaker support?

  A. At this point, since Hillmaker is an Access add-in, it only works with either native Access tables
     or linked SQL Server tables. I haven't had a chance to test it with other linked tables (e.g. MySQL
     or Oracle) but would guess it would work.


  Q. Where can I find some examples?

  A. Hillmaker distribution includes a sample database called SampleData.mdb that contains a raw data table
     as well as sample output tables from a Hillmaker run.


  Q. What are the future plans for Hillmaker?

  A. Developments planned for Hillmaker include:
     * Generalize to multiple category fields
     * Generalize to allow accumulation of "workload" instead of just occupancy. This will help with healthcare
       staffing studies.
     * Port it to OpenOffice environment (or some other open source platform)
     * Make the graphing spreadsheets more powerful and useful.


  Q. How do I report a Hillmaker bug?

  A. If you think you have found a bug in Hillmaker, please submit a bug report through the bug
     tracking system in SourceForge for the Hillmaker project.


  Q. How do I contribute to the Hillmaker development?

  A. TBD - I'm new to this open source development thing and I'm still figuring out best way to proceed.
     Suggestions welcome.
