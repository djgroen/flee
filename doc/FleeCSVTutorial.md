**Tutorial: Construction of refugee simulation**

**Detailed description of initial steps:**

**1.** Select a conflict scenario (country) and simulation (conflict) period

**2.** Download conflict data from [https://www.acleddata.com/data/acled-version-7-1997-2016/](https://www.acleddata.com/data/acled-version-7-1997-2016/)  (providing conflict data for countries in .xlsx format) for chosen country

**2.1** .xlsx file with conflict data will have various attributes illustrated in Table 1 below. 

Table 1: Conflict data in .xlsx file and required data to construct refugee simulation

<table>
  <tr>
    <td>Attribute name</td>
    <td>Description </td>
    <td>Required for simulation</td>
  </tr>
  <tr>
    <td>GWNO</td>
    <td>A numeric code for each individual country</td>
    <td></td>
  </tr>
  <tr>
    <td>EVENT_ID_CNTY</td>
    <td>An individual identifier by number and country acronym</td>
    <td></td>
  </tr>
  <tr>
    <td>EVENT_ID_NO_CNTY</td>
    <td>An individual numeric identifier</td>
    <td></td>
  </tr>
  <tr>
    <td>EVENT_DATE</td>
    <td>The data the event occurred in the format: 
yyyy-mm-dd</td>
    <td>+</td>
  </tr>
  <tr>
    <td>YEAR</td>
    <td>The year the event occurred</td>
    <td>+</td>
  </tr>
  <tr>
    <td>TIME_PRECISION</td>
    <td>A numeric code indicating the level of certainty of the date coded for the event </td>
    <td></td>
  </tr>
  <tr>
    <td>EVENT_TYPE</td>
    <td>The type of conflict event</td>
    <td>+</td>
  </tr>
  <tr>
    <td>ACTOR1</td>
    <td>The named actor involved in the event</td>
    <td></td>
  </tr>
  <tr>
    <td>ALLY_ACTOR_1</td>
    <td>The named actor allied with or identifying ACTOR1</td>
    <td></td>
  </tr>
  <tr>
    <td>INTER1</td>
    <td>A numeric code indicating the type of ACTOR2</td>
    <td></td>
  </tr>
  <tr>
    <td>ACTOR2</td>
    <td>The named actor involved in the event</td>
    <td></td>
  </tr>
  <tr>
    <td>ALLY_ACTOR_2</td>
    <td>The named actor allied with or identifying ACTOR2</td>
    <td></td>
  </tr>
  <tr>
    <td>INTER2</td>
    <td>A numeric code indicating the type of ACTOR2</td>
    <td></td>
  </tr>
  <tr>
    <td>INTERACTION</td>
    <td>A numeric code indicating the interaction between types of ACTOR1 and ACTOR2</td>
    <td></td>
  </tr>
  <tr>
    <td>COUNTRY </td>
    <td>The name of the country the event occurred in</td>
    <td></td>
  </tr>
  <tr>
    <td>ADMIN1</td>
    <td>The largest sub-national administrative region in which the event took place </td>
    <td>+</td>
  </tr>
  <tr>
    <td>ADMIN2</td>
    <td>The second largest sub-national administrative region in which the event took place</td>
    <td></td>
  </tr>
  <tr>
    <td>ADMIN3</td>
    <td>The third largest sub-national administrative region in which the event took place</td>
    <td></td>
  </tr>
  <tr>
    <td>LOCATION</td>
    <td>The location in which the event took place</td>
    <td>+</td>
  </tr>
  <tr>
    <td>LATITUDE</td>
    <td>The latitude of the location</td>
    <td>+</td>
  </tr>
  <tr>
    <td>LONGITUDE </td>
    <td>The longitude of the location</td>
    <td>+</td>
  </tr>
  <tr>
    <td>GEO_PRECISION</td>
    <td>A numeric code indicating the level of certainty of the location coded for the event</td>
    <td></td>
  </tr>
  <tr>
    <td>SOURCE</td>
    <td>The source of the event report</td>
    <td></td>
  </tr>
  <tr>
    <td>NOTES</td>
    <td>A short description of the event</td>
    <td></td>
  </tr>
  <tr>
    <td>FATALITIES</td>
    <td>The number of reported fatalities which occurred during the event</td>
    <td>+</td>
  </tr>
</table>


**2.2** Remove unrequired columns

**2.3** Revise **YEAR** column and target chosen simulation period of conflict scenario 

**2.4 EVENT_TYPE** column has 8 different variations: 

* **Battle **

    * **Battle-No change of territory**

    * **Battle-Government regains territory**

    * **Battle-Non-state actor overtakes territory**

* Violence against Civilians

* Remote Violence

* Riots and Protests

* State and Intergovernmental Forces

* Rebel Forces

* Political Militias

Here, focus on three types of **Battles **of conflict situation and remove other **EVENT_TYPE**.

**2.5 **After clearing some parts of conflict data file, target **FATALITIES **column** **and remove fatalities that are equal to 0 (zero). 

**2.6** To identify conflict locations for simulation, choose the first occurrence of each location but exclude syndicated (repeated) locations. 

Example: 

Table 2. Conflict locations for simulation		 	

<table>
  <tr>
    <td> …</td>
    <td>LOCATION</td>
    <td>FATALITIES</td>
  </tr>
  <tr>
    <td> …</td>
    <td>A</td>
    <td>3</td>
  </tr>
  <tr>
    <td> …</td>
    <td>B</td>
    <td>23</td>
  </tr>
  <tr>
    <td> …</td>
    <td>A</td>
    <td>38</td>
  </tr>
  <tr>
    <td> …</td>
    <td>C</td>
    <td>7</td>
  </tr>
  <tr>
    <td> …</td>
    <td>A</td>
    <td>38</td>
  </tr>
  <tr>
    <td> …</td>
    <td>C</td>
    <td>14</td>
  </tr>
  <tr>
    <td> …</td>
    <td>…</td>
    <td>…</td>
  </tr>
</table>


In this example, conflict zone A is repeated 

with fatalities of 3 and 38. Choose the highest 

and initial fatality (one of each location) as indicated in Table 2. 

A = 38

B = 23

C = 14

**3. **These filtering of conflict data from ACLED provides conflict location to use in simulation. Use these data construct first **locations.csv** file that has format demonstrated below. 

**locations.csv**

<table>
  <tr>
    <td>name</td>
    <td>region</td>
    <td>country</td>
    <td>lat</td>
    <td>long</td>
    <td>location_type</td>
    <td>conflict_date</td>
    <td>population/capacity</td>
  </tr>
  <tr>
    <td>A</td>
    <td>AA</td>
    <td>AAA</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict</td>
    <td>yyyy/mm/dd</td>
    <td></td>
  </tr>
  <tr>
    <td>B</td>
    <td>BB</td>
    <td>BBB</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict</td>
    <td>yyyy/mm/dd</td>
    <td></td>
  </tr>
  <tr>
    <td>C</td>
    <td>CC</td>
    <td>CCC</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict</td>
    <td>yyyy/mm/dd</td>
    <td></td>
  </tr>
  <tr>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
  </tr>
</table>


**4. **After identifying conflict location and producing **location.csv** fill the last column of population for conflict locations. Population distributions can be obtained from 

* [https://www.citypopulation.de](https://www.citypopulation.de) 

* or other sources

**5. **Identify destination locations i.e. camps from [UNHCR database](http://data2.unhcr.org/en/situations) and fill further** location.csv**

**location.csv**

<table>
  <tr>
    <td>name</td>
    <td>region</td>
    <td>country</td>
    <td>lat</td>
    <td>long</td>
    <td>location_type</td>
    <td>conflict_date</td>
    <td>population/capacity</td>
  </tr>
  <tr>
    <td>A</td>
    <td>AA</td>
    <td>AAA</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict_zone</td>
    <td>yyyy/mm/dd</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>B</td>
    <td>BB</td>
    <td>BBB</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict_zone</td>
    <td>yyyy/mm/dd</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>C</td>
    <td>CC</td>
    <td>CCC</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict_zone</td>
    <td>yyyy/mm/dd</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>Z</td>
    <td>ZZ</td>
    <td>ZZZ</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>camp</td>
    <td>-</td>
    <td></td>
  </tr>
  <tr>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
  </tr>
</table>


**5.1 **The last column in **location.csv** is capacity for camp location. Camp capacity is the highest number of refugees for each camp and obtained from individual camp csv files. 

Example: 							       Camp Z 

<table>
  <tr>
    <td>…</td>
    <td>…</td>
  </tr>
  <tr>
    <td>2015-03-31</td>
    <td>11470</td>
  </tr>
  <tr>
    <td>2015-06-02</td>
    <td>12405</td>
  </tr>
  <tr>
    <td>2015-07-24</td>
    <td>12405</td>
  </tr>
  <tr>
    <td>2015-08-31</td>
    <td>11359</td>
  </tr>
  <tr>
    <td>2015-09-30</td>
    <td>8129</td>
  </tr>
  <tr>
    <td>…</td>
    <td>…</td>
  </tr>
</table>


CampZ.csv has the highest number of refugees of

**12405**** **on 2015-06-02 that is camp capacity in location.csv for Camp Z. 

* It is also important to highlight that refugee registrations for camps have corrections to overcome inaccurate registrations. To consider this factor in simulation, identify level 1 registration that is decline in refugee numbers. In the case of this example, there is drop from **11359 to 8129 **and thus take into account new registration date – **2015-09-30. **

**6. **Identified conflict zones and camps provide origin and destination locations to determine the main routes through which refugees flee. Use [http://www.bing.com/maps](http://www.bing.com/maps) (or other mapping services) to connect conflict zones and camps and add additional locations as town to **location.csv** as illustrated below:

**location.csv**

<table>
  <tr>
    <td>name</td>
    <td>region</td>
    <td>country</td>
    <td>lat</td>
    <td>long</td>
    <td>location_type</td>
    <td>conflict_date</td>
    <td>population/capacity</td>
  </tr>
  <tr>
    <td>A</td>
    <td>AA</td>
    <td>ABC</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict_zone</td>
    <td>yyyy/mm/dd</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>B</td>
    <td>BB</td>
    <td>ABC</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict_zone</td>
    <td>yyyy/mm/dd</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>C</td>
    <td>CC</td>
    <td>ABC</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>conflict_zone</td>
    <td>yyyy/mm/dd</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>Z</td>
    <td>ZZ</td>
    <td>ZZZ</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>camp</td>
    <td>-</td>
    <td>Xxx</td>
  </tr>
  <tr>
    <td>N</td>
    <td>NN</td>
    <td>ABC</td>
    <td>xxx</td>
    <td>xxx</td>
    <td>town</td>
    <td>-</td>
    <td>-</td>
  </tr>
  <tr>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
  </tr>
</table>


Construct network map and create **routes.csv** file for simulation, which has the following format:

**routes.csv								              Network map**

<table>
  <tr>
    <td>name1</td>
    <td>name2</td>
    <td>distance [km]</td>
    <td>forced_redirection</td>
  </tr>
  <tr>
    <td>A</td>
    <td>B</td>
    <td>x1</td>
    <td></td>
  </tr>
  <tr>
    <td>B</td>
    <td>C</td>
    <td>x2</td>
    <td></td>
  </tr>
  <tr>
    <td>A</td>
    <td>C</td>
    <td>x3</td>
    <td></td>
  </tr>
  <tr>
    <td>B</td>
    <td>N</td>
    <td>x4</td>
    <td></td>
  </tr>
  <tr>
    <td>C</td>
    <td>N</td>
    <td>x3</td>
    <td></td>
  </tr>
  <tr>
    <td>N</td>
    <td>Z</td>
    <td>x5</td>
    <td></td>
  </tr>
  <tr>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td></td>
  </tr>
</table>


* **forced_redirection **refers to redirection from source location (can be town or camp) to destination location (mainly camp) and source location indicated as forwarding_hub. The value of 0 indicates no redirection, 1 indicates redirection (from name2) to name1and 2 corresponds to redirection (from name1) to name2. 

**7. **Another required csv file is **closures.csv **that describes camp or border closure events at location or country levels.

**closures.csv**

<table>
  <tr>
    <td>closure_type*</td>
    <td>name1</td>
    <td>name2</td>
    <td>closure_start = 0*</td>
    <td>closure_end = -1*</td>
  </tr>
  <tr>
    <td>- location</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td>- country</td>
    <td></td>
    <td></td>
    <td></td>
    <td></td>
  </tr>
  <tr>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
    <td>…</td>
  </tr>
</table>


***closure_type **has 2 types: *location* corresponding camp closure and *country* referring to border closure

***closure_start** and **closure_end** are given as integers, counting the number of days after the simulation start. The value of 0 indicates the start, while -1 indicates the end of the simulation.

