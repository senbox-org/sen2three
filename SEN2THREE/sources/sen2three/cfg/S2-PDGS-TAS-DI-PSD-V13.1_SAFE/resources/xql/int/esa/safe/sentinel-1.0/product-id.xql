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

import module namespace util = "http://www.esa.int/safe/xql/util"
              at "util-module.xql";

declare variable $manifest_node as node()? external;
declare variable $manifest_crc16 as xs:string? external;
declare variable $originating_facility as xs:string? external;

util:getSafeProductId ($manifest_node,$manifest_crc16,$originating_facility)
