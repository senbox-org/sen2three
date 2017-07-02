(:
   SAFE - Standard Archive Format for Europe
   Copyright (C) 2004,2005,2006,2007,2008,2009,2010 European Space Agency (ESA)
   Copyright (C) 2004,2005,2006,2007,2008,2009,2010 GAEL Consultant
   GNU Lesser General Public License (LGPL)
   
   This file is part of SAFE
   
   SAFE is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   SAFE is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.
   
   You should have received a copy of the GNU Lesser General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
:)

module namespace util = "http://www.esa.int/safe/xql/util";

declare variable $util:implementationTitle as xs:string? external;
declare variable $util:implementationVersion as xs:string? external;
declare variable $util:javaImplementationTitle as xs:string? external;
declare variable $util:javaImplementationVersion as xs:string? external;

declare variable $util:pi := 3.141592653589793;

(: The location of the product definition pre-suppose that base URI has been
 : set to $SAFE_TRANSFORM_HOME/resources/xsd/int/esa/safe/<version>
 : A better solution may be to make the path relative to an external variable
 : to be provided by the caller or the importing module.
 :)
declare variable $util:product-definition := 
   ../../../../../../product-definition.xml;

(: Returns the product (whenever Aux, Level 0, 1 or 2) version matching the
 : input product name.
 :)
declare function util:getProductVersion ($product_name as xs:string) as xs:string
{
   let $product := $util:product-definition/
      resources/*/product[matches($product_name, data(@regex))]
   return

   if ($product)
   then
      data($product/@ver)
   else
      error(concat("Unknown product: ", $product_name, " (util:getProductVersion)"))
};

declare function util:getProductTypeVersion ($product_name as xs:string,
                                           $product_id as xs:string)
                                           as xs:string
{
   let $product := 
      if ($product_id = "") (: no product_id :)
      then
         $util:product-definition/
         resources/*/product[matches($product_name, data(@regex))]
      else (: there is a product_id :)
         $util:product-definition/
         resources/*/product[$product_id = data(@ID)]
   return

   if ($product)
   then
      data($product/@ver)
   else
      error(concat("Unknown product: ", $product_name, " (util:getProductTypeVersion)"))
};

declare function util:getProductId ($xfdu_node as node()) as xs:string
{
   let $ver := data($xfdu_node/@*[name(.) = "version"])
   let $product := $util:product-definition/resources/*/product
                   [$ver = data(@ver)]
   return
   if($product)
   then data($product/@ID)
   else error(concat("Unknown product version: ",$ver," (util:getProductId)"))
};

declare function util:buildFamilyName ($abbreviation as xs:string,
                                       $content as xs:string) as node()
{
  <familyName abbreviation="{$abbreviation}">{$content}</familyName>
};

declare function util:formatDateTime ($datetime as xs:string) as xs:string
{
  let $splited := fn:tokenize($datetime,"-")
  let $day := $splited[1]
  let $month := util:formatMonth($splited[2])
  let $year := fn:tokenize($splited[3]," ")[1]
  let $time := fn:tokenize($splited[3]," ")[2]

  return concat($year,"-",$month,"-",$day,"T",$time,"Z")
};

declare function util:formatMonth ($month as xs:string) as xs:string
{
  if($month = "JAN") then "01"
  else if($month = "FEB") then "02"
  else if($month = "MAR") then "03"
  else if($month = "APR") then "04"
  else if($month = "MAY") then "05"
  else if($month = "JUN") then "06"
  else if($month = "JUL") then "07"
  else if($month = "AUG") then "08"
  else if($month = "SEP") then "09"
  else if($month = "OCT") then "10"
  else if($month = "NOV") then "11"
  else if($month = "DEC") then "12"
  else error(concat("Cannot convert: ", $month))
};

declare function util:stringToDateTime($datetime as xs:string) as xs:dateTime
{
   let $splited1 := fn:tokenize($datetime,"T")
   let $splited2 := fn:tokenize($splited1[1],"-")
   let $month :=
      if($splited2[2] = "01") then "JAN"
      else if($splited2[2] = "02") then "FEB"
      else if($splited2[2] = "03") then "MAR"
      else if($splited2[2] = "04") then "APR"
      else if($splited2[2] = "05") then "MAY"
      else if($splited2[2] = "06") then "JUN"
      else if($splited2[2] = "07") then "JUL"
      else if($splited2[2] = "08") then "AUG"
      else if($splited2[2] = "09") then "SEP"
      else if($splited2[2] = "10") then "OCT"
      else if($splited2[2] = "11") then "NOV"
      else if($splited2[2] = "12") then "DEC"
      else error("Unknown month number")
   let $datetime_string := concat($splited2[3],"-",$month,"-",$splited2[1]," ",replace($splited1[2],"Z",""))
   return xs:dateTime($datetime_string)
};

declare function util:getSafeProductId ($xfdu_node as node(),
                                        $manifest_crc16 as xs:string,
                                        $originating_facility as xs:string) as xs:string
{

  let $nssdcid := data($xfdu_node/metadataSection/metadataObject[data(@ID) = "platform"]/metadataWrap/xmlData/platform/nssdcIdentifier)

  let $mission_id :=

     if ($nssdcid) then
        if      ($nssdcid = "2002-009A") then "EN01"
        else if ($nssdcid = "1995-021A") then "ER02"
        else if ($nssdcid = "1991-050A") then "ER01"
        else error(concat("Unknown NSSDCID platform identifier: ", $nssdcid))
        else error(concat("Null NSSDCID platform identifier."))

  let $product_id := util:getProductId($xfdu_node)

  let $acquisition_period := $xfdu_node/metadataSection/metadataObject[data(@ID) = "acquisitionPeriod"]/metadataWrap/xmlData/acquisitionPeriod

  let $validity_start :=
     if(data($acquisition_period/startTime)) then fn:substring(fn:replace(data($acquisition_period/startTime),"(:|-)",""),1,15)
  else trace("_______________","Cannot find validity start time")

  let $validity_stop :=
  if(data($acquisition_period/stopTime)) then fn:substring(fn:replace(data($acquisition_period/stopTime),"(:|-)",""),1,15)
  else trace("_______________","Cannot find validity stop time")

  let $orbit_reference := ($xfdu_node/metadataSection/metadataObject[matches(data(@ID),".*OrbitReference")]/metadataWrap/xmlData/orbitReference)[1]

  let $absolute_orbit :=
  if($orbit_reference) then
     xs:string(xs:int(data($orbit_reference/orbitNumber[data(@type) = "start"])))
  else trace("","Cannot find absolute orbit number (no orbit reference)")

  let $separator := "_"

  return concat($mission_id,$separator,
                $product_id,$separator,
                $validity_start,$separator,
                $validity_stop,$separator,
                $originating_facility,$separator,
                $absolute_orbit,$separator,
                $manifest_crc16,".",
                "SAFE")
};

declare function util:getVersion($dummy) as xs:string
{
   fn:replace(fn:substring-after("$Name:  $", "safe-transform-"),
      " \$", "")
};

declare function util:buildFacilityNode ($name as xs:string,
                                         $organisation as xs:string?,
                                         $site as xs:string?,
                                         $country as xs:string?,
                                         $soft as node()?) as node()
{
   <safe:facility xmlns:safe="http://www.esa.int/safe/1.3"
                  name="{$name}"
                  organisation="{ $organisation}"
                  site="{$site}"
                  country="{$country}">
      {$soft}
   </safe:facility>
};

declare function util:degreeToRadian10E-6To1($value as xs:integer) as xs:string
{
   xs:string((xs:double($value) * $util:pi * 0.000001) div 180)
};

declare function util:degreeToRadian($value as xs:integer) as xs:string
{
   xs:string(($value * $util:pi) div 180)
};

declare function util:trim($var as xs:string) as xs:string
{
   replace($var, "^ +| +$", "")
};

declare function util:treeToList ($sequence)
{
   for $item in $sequence
   return
      (
       $item,
       util:treeToList ($item/*)
      )
};

declare function util:killStringClone ($sequence)
{
   for $item at $index in $sequence
   where fn:count(
      util:searchStringClone($item, $index, $sequence)) = 0
   return $item
};

declare function util:searchStringClone ($item,
                                         $index as xs:int,
                                         $sequence)
{
   for $suspect in $sequence
   where position() > $index
   and data($suspect) = data($item)
      return "detected_clone"
};

declare function util:addTableRows($wild_card,
                                   $level) as node()*
{
   for $item at $index in $wild_card
   return
      let $prefix :=
         if ($item/@ns) then concat(data($item/@ns), ":")
         else
         if ($item/@type = "attribute") then "@"
         else ()
      return (
      <row>
         <entry><classname>{concat($level,
                                   $prefix,
                                   fn:name($item))}</classname></entry>
         {
         if ($item/@*[name() = "value"])
         then
         <entry>{data($item/@*[name() = "value"])}</entry>
         else
         <entry/>
         }
         <entry align='center'>{data($item/@occurs)}</entry>
      </row>,
      util:addTableRows($item/*, concat($level, ". "))
      )
};

declare function util:upperCase($name as xs:string) as xs:string
{
   let $seq_a := replace($name, "a", "A")
   let $seq_b := replace($seq_a, "b", "B")
   let $seq_c := replace($seq_b, "c", "C")
   let $seq_d := replace($seq_c, "d", "D")
   let $seq_e := replace($seq_d, "e", "E")
   let $seq_f := replace($seq_e, "f", "F")
   let $seq_g := replace($seq_f, "g", "G")
   let $seq_h := replace($seq_g, "h", "H")
   let $seq_i := replace($seq_h, "i", "I")
   let $seq_j := replace($seq_i, "j", "J")
   let $seq_k := replace($seq_j, "k", "K")
   let $seq_l := replace($seq_k, "l", "L")
   let $seq_m := replace($seq_l, "m", "M")
   let $seq_n := replace($seq_m, "n", "N")
   let $seq_o := replace($seq_n, "o", "O")
   let $seq_p := replace($seq_o, "p", "P")
   let $seq_q := replace($seq_p, "q", "Q")
   let $seq_r := replace($seq_q, "r", "R")
   let $seq_s := replace($seq_r, "s", "S")
   let $seq_t := replace($seq_s, "t", "T")
   let $seq_u := replace($seq_t, "u", "U")
   let $seq_v := replace($seq_u, "v", "V")
   let $seq_w := replace($seq_v, "w", "W")
   let $seq_x := replace($seq_w, "x", "X")
   let $seq_y := replace($seq_x, "y", "Y")
   let $seq_z := replace($seq_y, "z", "Z")
   return $seq_z
};

declare function util:lowerCase($name as xs:string) as xs:string
{
   let $seq_a := replace($name, "A", "a")
   let $seq_b := replace($seq_a, "B", "b")
   let $seq_c := replace($seq_b, "C", "c")
   let $seq_d := replace($seq_c, "D", "d")
   let $seq_e := replace($seq_d, "E", "e")
   let $seq_f := replace($seq_e, "F", "f")
   let $seq_g := replace($seq_f, "G", "g")
   let $seq_h := replace($seq_g, "H", "h")
   let $seq_i := replace($seq_h, "I", "i")
   let $seq_j := replace($seq_i, "J", "j")
   let $seq_k := replace($seq_j, "K", "k")
   let $seq_l := replace($seq_k, "L", "l")
   let $seq_m := replace($seq_l, "M", "m")
   let $seq_n := replace($seq_m, "N", "n")
   let $seq_o := replace($seq_n, "O", "o")
   let $seq_p := replace($seq_o, "P", "p")
   let $seq_q := replace($seq_p, "Q", "q")
   let $seq_r := replace($seq_q, "R", "r")
   let $seq_s := replace($seq_r, "S", "s")
   let $seq_t := replace($seq_s, "T", "t")
   let $seq_u := replace($seq_t, "U", "u")
   let $seq_v := replace($seq_u, "V", "v")
   let $seq_w := replace($seq_v, "W", "w")
   let $seq_x := replace($seq_w, "X", "x")
   let $seq_y := replace($seq_x, "Y", "y")
   let $seq_z := replace($seq_y, "Z", "z")
   return $seq_z
};

declare function util:concatSequence($sequence as item()*) as xs:string
{
   if (count($sequence) = 0) then ""
   else
   if (count($sequence) = 1) then $sequence
   else
   concat($sequence[1],
          util:concatSequence(for $i in $sequence
                              where position() > 1
                              return $i))
};

declare function util:concatSequenceSpaceSeparator ($sequence)
                 as xs:string
{
   if (count($sequence) = 0) then ""
   else
   if (count($sequence) = 1) then $sequence
   else
   concat($sequence[1], " ",
          util:concatSequenceSpaceSeparator(for $i in $sequence
                                            where position() > 1
                                            return $i))
};

declare function util:concatSequenceDashSeparator ($sequence)
                 as xs:string
{
   if (count($sequence) = 0) then ""
   else
   if (count($sequence) = 1) then $sequence
   else
   concat($sequence[1], "-",
          util:concatSequenceDashSeparator(for $i in $sequence
                                           where position() > 1
                                           return $i))
};

declare function util:foo-bar_to_fooBar($input_name as xs:string) as xs:string
{
   let $sequenced_name := fn:tokenize($input_name, "-")
   return

   if (count($sequenced_name) = 1)
   then $sequenced_name
   else

      let $first_item := $sequenced_name[1]

      let $inter_sequence :=
         for $item at $index in $sequenced_name
         where $index != 1
         return
            concat(util:upperCase(substring($item, 1, 1)),
                   substring($item, 2))

      return concat($first_item,
                    util:concatSequence($inter_sequence))
};

declare function util:foo-bar_to_FooSpaceBar($input_name as xs:string)
                 as xs:string
{
   let $sequenced_name := fn:tokenize($input_name, "-")
   return

   if (count($sequenced_name) = 1)
   then concat(util:upperCase(substring($sequenced_name, 1, 1)),
               substring($sequenced_name, 2))
   else

      let $inter_sequence :=
         for $item in $sequenced_name
         return
            concat(util:upperCase(substring($item, 1, 1)),
                   substring($item, 2))

      return concat(util:concatSequenceSpaceSeparator($inter_sequence))
};

declare function util:FOOSpaceBarSpace1_to_foo-bar-1 ($input_name as xs:string)
                 as xs:string
{
   let $sequenced_name := fn:tokenize($input_name, " ")
   return

   if (count($sequenced_name) = 1)
   then util:lowerCase($sequenced_name)
   else

      let $inter_sequence :=
         for $item in $sequenced_name
         return util:lowerCase($item)

      return concat(util:concatSequenceDashSeparator($inter_sequence))
};

declare function util:createErrorSection ($message as xs:string)
{
<section>
<title>ERROR</title>
   <para>
   {concat("ERROR : ", $message)}
   </para>
</section>
};
