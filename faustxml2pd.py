#!/usr/bin/env python
# a script for converting a faust xml output to puredata, 
# hacked together from http://puredata.info/docs/developer/PdFileFormat
# Nicola Montecchio - http://www.nicolamontecchio.com - May 2012
from xml.dom.minidom import parse, parseString
import sys
import argparse

def slider(attrs,x0,y0,prefix,next_obj_id,slider_type) :
	#X obj 50 38 vsl 15 128 0 127 0 0 empty empty empty 0 -8 0 8 -262144 -1 -1 0 1;
	w,h = (60,10) if slider_type == 'hsl' else (10,60)
	w_pixel = w if slider_type == 'hsl' else h
	minval = float(attrs[2][:-1]) # take out trailing 'f' in e.g., 1.0f or 2e+01f
	maxval = float(attrs[3][:-1])
	inival = float(attrs[1][:-1])
	return ['#X obj %d %d %s %d %d %f %f 0 1 empty empty %s 0 -8 0 10 -262144 -1 -1 %d 1;' % 
	           (x0, y0, slider_type, w, h, minval, maxval, attrs[0], 
						 int(inival*100.*w_pixel/(maxval-minval)))]        +      nentry(attrs,x0,y0+h+10,prefix,
						 next_obj_id+1,False)        +          ['#X connect %d 0 %d 0;' % (next_obj_id, next_obj_id+1)]
	
def vslider(attrs,x0,y0,prefix,next_obj_id):
	return slider(attrs,x0,y0,prefix,next_obj_id,'vsl')

def hslider(attrs,x0,y0,prefix,next_obj_id):
	return slider(attrs,x0,y0,prefix,next_obj_id,'hsl')

def button(attrs,x0,y0,prefix,next_obj_id) :
	return ['#X obj %d %d tgl 15 1 empty empty %s 0 -8 0 10 -262144 -1 -1 1 0;' % (x0,y0,attrs[0]), 
	       '#X msg %d %d %s%s \\$1;' % (x0, y0+20, prefix, attrs[0]),
				 '#X connect %d 0 %d 0;' % (next_obj_id, next_obj_id+1)]	

def nentry(attrs,x0,y0,prefix,next_obj_id,printlabel = True) :
	minval = float(attrs[2][:-1]) # take out trailing 'f' in e.g., 1.0f or 2e+01f
	maxval = float(attrs[3][:-1])
	inival = float(attrs[1][:-1])
	return ['#X obj %d %d nbx 6 14 %f %f 0 1 empty empty %s 0 -8 0 10 -262144 -1 -1 %f 256;' % 
	                (x0, y0, minval, maxval, attrs[0] if printlabel else 'empty', inival),
	        '#X msg %d %d %s%s \\$1;' % (x0, y0+20, prefix, attrs[0]),
					'#X connect %d 0 %d 0;' % (next_obj_id, next_obj_id+1)] 

def is_connect_msg(s):
	return s.find('#X connect') == 0

def is_obj_msg(s):
	return not is_connect_msg(s)

if __name__ == '__main__':
	prefix = sys.argv[-1] if len(sys.argv) > 2 else ''
	output_object = sys.argv[1]
	dom = parse(sys.stdin)
	tag_order = {'hslider' : ['label','init','min','max'],
	             'vslider' : ['label','init','min','max'],
	             'nentry'  : ['label','init','min','max'],
		           'button'  : ['label']}
	fa2pd = {'button':button, 'vslider':vslider, 'hslider':hslider, 'nentry':nentry}
	widgets = dom.getElementsByTagName('widget')
	collected_widgets = []
	for widget in widgets :
		wtype = widget.getAttribute('type')
		w = [wtype]
		for tag in tag_order[wtype] :
			el = widget.getElementsByTagName(tag)[0]
			w.append(el.firstChild.data)
		collected_widgets.append(w)
	
	### VVV ### experimental layout code (very naive) ### VVV ### 
	next_obj_id = 0
	canvas_size = (500,300)
	x_width = 100
	y_width = 100
	x = 15
	y = 15
	print '#N canvas 0 0 %d %d;' % canvas_size
	obj_lines     = []
	connect_lines = []
	for cw in collected_widgets :
		widget_lines   = fa2pd[cw[0]](cw[1:],x,y,prefix,next_obj_id)
		widget_lines   = widget_lines if widget_lines else []   # [] if object type is not implemented yet # TODO remove when finished
		widget_objects = list(filter(is_obj_msg, widget_lines))
		obj_lines     += widget_objects
		connect_lines += list(filter(is_connect_msg, widget_lines))
		if len(widget_lines) > 0 :
			x += x_width
			if (x >= canvas_size[0] - x_width) :
				x = 15
				y += y_width
		next_obj_id += len(widget_objects)
	last_obj_id = next_obj_id
	obj_lines.append('#X obj %d %d %s;' % (0, y+y_width, output_object))   # collector outlet
	obj_lines_with_obj_no = [(obj_lines[i],i) for i in range(len(obj_lines))]
	outlet_connect_lines = list(map(lambda ol : '#X connect %d 0 %d 0;' % (ol[1], last_obj_id), 
	                                   filter(lambda x : x[0].find('#X msg') == 0,obj_lines_with_obj_no)))
	for l in obj_lines + connect_lines + outlet_connect_lines : print l

