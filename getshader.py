#!/usr/bin/env python3

# Standalone Shadertoy
# Copyright (C) 2014 Simon Budig <simon@budig.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, json, urllib.request, urllib.parse
import ntpath, os

overwriteGLSL = True

shaderinfo = """\
// Shader downloaded from https://www.shadertoy.com/view/%(id)s
// written by shadertoy user %(username)s
//
// Name: %(name)s
// Description: %(description)s
"""

shaderdecls = """
layout (location = 0) out vec4 fragColor;
uniform vec3      iResolution;           // viewport resolution (in pixels)
uniform float     iGlobalTime;           // shader playback time (in seconds)
uniform float     iChannelTime[4];       // channel playback time (in seconds)
uniform vec3      iChannelResolution[4]; // channel resolution (in pixels)
uniform vec4      iMouse;                // mouse pixel coords. xy: current (if MLB down), zw: click
uniform vec4      iDate;                 // (year, month, day, time in secs)
uniform float     iSampleRate;           // sound sample rate (i.e., 44100)
#define iChannel0 sTD2DInputs[0]
#define iChannel1 sTD2DInputs[1]
#define iChannel2 sTD2DInputs[2]
#define iChannel3 sTD2DInputs[3]
#define iTime iGlobalTime
//if it's cube texture, then replace sTD2DInputs with sTDCubeInputs
\n"""

# see https://www.shadertoy.com/js/effect.js?v=8

shadermain = """\n
void main ()
{
  vec4 color = vec4 (0.0, 0.0, 0.0, 1.0);
  mainImage (color, gl_FragCoord.xy);
  color.w = 1.0;
  fragColor = color;
}
"""

def get_shader (id):
   url = 'https://www.shadertoy.com/shadertoy'
   headers = { 'Referer' : 'https://www.shadertoy.com/' }
   values  = { 's' : json.dumps ({'shaders' : [id]}) }

   data = urllib.parse.urlencode (values).encode ('utf-8')
   req  = urllib.request.Request (url, data, headers)
   response = urllib.request.urlopen (req)
   shader_json = response.read ().decode ('utf-8')

   j = json.loads (shader_json)
   f = open ("/tmp/current-shader.json", "w")
   f.write (json.dumps (j, indent=2))
   f.close ()

   assert (len (j) == 1)

   for s in j:
      name = s["info"]["name"]
      if not os.path.exists(name):
         os.mkdir(name)
      os.chdir(name)
      desc = s["info"]["description"]
      desc = "".join (desc.split("\r"))
      desc = "\n//    ".join (desc.split("\n"))
      s["info"]["description"] = desc
      info = s["info"]

      p_index = 1
      for p in s["renderpass"]:
         if p["code"] != None:
            code = (p["code"])
            f = None
            attempt = 0
            while f == None:
               if overwriteGLSL:
                  fname = "%s-pass%d.glsl" % (name, p_index)
                  f = open (fname, "w")
               else:
                  try:
                     if attempt == 0:
                        fname = "%s-pass%d.glsl" % (name, p_index)
                     else:
                        fname = "%s-pass%d.glsl.%d" % (name, p_index, attempt)
                     f = open (fname, "x")

                  except FileExistsError:
                     attempt += 1
                     if attempt > 10:
                        print ("clean out your files please...", file=sys.stderr)
                        sys.exit (0)

            f.write (shaderinfo % info)
            f.write (shaderdecls)
            f.write (code)
            f.write (shadermain)
            f.close ()
            print ("wrote shader to \"%s\"" % fname, file=sys.stderr)

         if p["inputs"] != None:
            for i in p["inputs"]:
               if i["filepath"] != None:
                  try:
                     if "http" not in i["filepath"]:
                        fileurl = 'https://www.shadertoy.com' + i["filepath"]
                     else:
                        fileurl = i["filepath"]
                     filename, file_extension = os.path.splitext(ntpath.basename(fileurl))
                     newFileName = "Pass%d_iChannel%d%s" % (p_index, i["channel"], file_extension)
                     if not os.path.exists(newFileName):
                        urllib.request.urlretrieve(fileurl, newFileName)
                  except:
                     print ("failed to download:" + fileurl)
         p_index += 1
               
      
if __name__ == '__main__':
   if len (sys.argv) < 2:
      print ("Usage: %s <id>" % sys.argv[0], file=sys.stderr)

   for id in sys.argv[1:]:
      id = id.split("/")[-1]
      get_shader (id)
      

