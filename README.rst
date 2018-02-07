##################
 OSC Cloud Builder
##################

The **OCB** project provides tools as snippets and modules.

************
Introduction
************

**OCB** is a set of boto connectors, generic tools and samples scripts to be used to ease the build of platforms.

******
Setup
******

Cloud account setup
=====================
There are 2 ways to configure OCB: environment variables or configuration file



Environment variables
---------------------
Setup of the following variables:

    - export AWS_ACCESS_KEY_ID=XXXX424242XXXX
    - export AWS_SECRET_ACCESS_KEY=YYYYY4242YYYYY

If you want to connect to ICU for special API call such as ResetAccountPassword  (see http://docs.outscale.com/api_icu/operations/Action_ResetAccountPassword_post.html#_api_icu-action_resetaccountpassword_post) you must setup both login and password
    - export ICU_LOGIN=ZZZZ424242ZZZZ
    - export ICU_PASSWORD=AAAAA4242AAAAA

Then configure the endpoints
    - export FCU_ENDPOINT=fcu.<REGION_NAME>.outscale.com
    - export LBU_ENDPOINT=lbu.<REGION_NAME>.outscale.com
    - export EIM_ENDPOINT=eim.<REGION_NAME>.outscale.com
    - export OSU_ENDPOINT=osu.<REGION_NAME>.outscale.com
    - export ICU_ENDPOINT=icu.<REGION_NAME>.outscale.com


File configuratoin
---------------------
You can use a .ini file to setup multiple accounts.

To do so create a file like
::
	 [first_account]
	 access_key_id = xxxx
	 secret_access_key = yyyy
	 eim_endpoint = eim.eu-west-2.outscale.com
	 fcu_endpoint = fcu.eu-west-2.outscale.com
	 lbu_endpoint = lbu.eu-west-2.outscale.com
	 osu_endpoint = osu.eu-west-2.outscale.com

	 [second_account]
	 access_key_id = xxxx
	 secret_access_key = yyyy
	 eim_endpoint = eim.us-east-2.outscale.com
	 fcu_endpoint = fcu.us-east-2.outscale.com
	 osu_endpoint = osu.us-east-2.outscale.com



How to use it
===============

From package
--------------
Just import OCBase

::

   >>>from osc_cloud_builder.OCBase import OCBase

From repository
----------------
If you are not using this project as a package, go to root of this project and configure your PYTHONPATH. At the root of the project directory run:

::

   $>export PYTHONPATH=$PYTHONPATH:$PWD/osc_cloud_builder
   $>python
   >>>from OCBase import OCBase


Quick start:
--------------

::

   >>>ocb = OCBase()
   >>>print ocb.fcu.get_only_instances()
   >>>print ocb.eim.get_user()
   >>>print ocb.lbu.get_all_load_balancers()
   >>>print ocb.icu.get_catalog()


Quick start with multiple accounts:
-------------------------------------
::
	 >>>ocb = OCBase.OCBase('first_account', ['/home/centos/my_accounts.ini'])
	 >>>print ocb.fcu.get_only_instances()
	 >>>ocb.reload('second_account')
	 >>>print ocb.fcu.get_only_instances()


*******
Helpers
*******

OCB provides you modules under *sample* and *tools* to help you doing basic things.


***********
Disclaimer
***********

This software is provided not guarantee by Outscale.
