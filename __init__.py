# ##### BEGIN GPL LICENSE BLOCK #####
#
#  BGE Post-Processing Filters, a Blender addon
#  (c) 2016 Tim Crellin (Thatimst3r)
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {"name": "Post-Processing Filters", "category": "Game Engine", "author": "Tim Crellin (Thatimst3r) contributions by Martins Upitis, Smoking_mirror, TwisterGE, cyborg_ar, youle, kitebizelt", "blender": (2,77,0), "location": "Game Render Panel", "description":"Provides 20 different post-processing effects.","warning": "","wiki_url":"", "tracker_url": "", "version":(1,5)}

import bpy
import os
from bpy.props import *

#Main panel
class FilterPanel(bpy.types.Panel):
    bl_label = "Post-Processing Filters"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = 'render'
    
    def draw(self, context):
        scn = context.scene
        if bpy.context.mode == 'OBJECT':
            layout = self.layout
            if bpy.context.scene.render.engine != 'BLENDER_GAME':
                row = layout.row()
                layout.label(" Select Blender Game renderer to use addon", icon = 'ERROR')
            elif len(context.selected_objects) != 1 or context.selected_objects[0].type != 'CAMERA':
                row = layout.row()
                layout.label(' To add or remove filters select a camera', icon = 'ERROR')
                
            else:
                layout.label(' Filter order: Shading > Glow > Color', icon = 'INFO')
                layout.row()
                layout.prop(scn, 'Chosen_filter')
                if scn.Chosen_filter == 'MOTION BLUR':
                    result = check_mblur_remove()
                else:
                    result = check_filters(scn.Chosen_filter)
                
                descriptions = {'D.O.F.':'Adds depth of field', 'S.S.A.O.': 'Darkens edges of objects', 'BLOOM':'Adds glow to bright objects', 'NOISE':'Adds noise to the screen', 'VIGNETTE':'Darkens the edges of the screen', 'RETINEX':'Enhances contrast, maintains color.','WATER':'Underwater distortion effect', 'CHROMATIC ABERRATION':'Coloured Fringing', 'BLOOM X':'Adds X shaped glow to objects', 'BLEACH':'Horror game filter. Low saturation, high contrast.', 'BARREL':'Adds buldge distortion to the centre of the screen', 'F.X.A.A.':'Efficient Anti-Aliasing', 'GAMEBOY COLOR':'Gameboy style pixelization.', 'LEVELS':'Color channel remapping with curves', 'NIGHT VISION':'Infared style night vision', 'RADIAL BLUR':'Adds blur around the edges of the screen','TOON':'Adds toon outline', 'H.D.R.':'Adjusts light levels to suit environment', 'MOTION BLUR':'Adds blur when moving fast','GAMMA':'Brightens dark spaces'}
                if result == True and scn.Chosen_filter =='D.O.F.' or scn.Chosen_filter =='S.S.A.O.' and result == True:
                    row = layout.row()
                    layout.label('Make sure Camera clipping is the same in filter script.',icon='ERROR')
                elif result == True and scn.Chosen_filter == 'TOON':
                    row = layout.row()
                    layout.label('Keep "line_size" property below 1',icon='ERROR')
                elif result == True and scn.Chosen_filter == 'MOTION BLUR':
                    row = layout.row()
                    layout.label('To change blur see "distance" prop on Mblur_empty', icon='ERROR')
                
                row = layout.row()
                col = row.column()
                col.label('Description:   ' + descriptions[scn.Chosen_filter])
                
                row = layout.row()
                col = row.column()
                col.operator('remove.filter', icon='CANCEL')
                
                col = row.column()
                col.operator('add.filter',icon='PLUS')
        
class Remove_Filter(bpy.types.Operator):
    bl_idname = "remove.filter"
    bl_label = "Remove Filter"
    
    @classmethod
    def poll(cls, context):
        scn = context.scene
        if scn.Chosen_filter == 'MOTION BLUR':
            return check_mblur_remove()
        else:
            return check_remove(scn.Chosen_filter)
    
    def execute(self,context):
        scn = context.scene
                
        set_filter = scn.Chosen_filter
        removeFilter(set_filter)
        if set_filter == 'MOTION BLUR':
            report_string = 'Removed MOTION BLUR from '+scn.name
        else:
            report_string = 'Removed '+set_filter+' from '+context.selected_objects[0].name
        self.report({'INFO'}, report_string)        
        return{'FINISHED'}
    
class Add_Filter(bpy.types.Operator):
    bl_idname = "add.filter"
    bl_label = "Add Filter"
    
    
    @classmethod
    def poll(cls, context):
        scn = context.scene
        if scn.Chosen_filter == 'MOTION BLUR':
            return not check_mblur_remove()
        else:
            return not check_filters(scn.Chosen_filter)
        
    def execute(self, context):
        scn = context.scene
        
        set_filter = scn.Chosen_filter

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        if set_filter != 'MOTION BLUR':
            addFilter(set_filter,directory, scn.index_num)
        else:
            addMblur(directory, scn.index_num)
        scn.index_num += 1
        if scn.Chosen_filter != 'MOTION BLUR':
            report_string = 'Added '+set_filter+' to '+context.selected_objects[0].name
        else:
            report_string = 'Added MOTION BLUR to ' + scn.name
        self.report({'INFO'}, report_string)
        return{'FINISHED'}

#add mblur
def addMblur(directory, pass_num):
    used_camera = bpy.context.active_object
    bpy.ops.object.empty_add(type='SPHERE',view_align=False, location=(0,0,0))
    bpy.context.active_object.name = 'Mblur_empty'
    bpy.ops.object.game_property_new(name='distance')
    bpy.context.active_object.game.properties['distance'].value = 0.15
    for i in range(16):
        bpy.ops.object.game_property_new(name='x'+str(i))
    for j in range(16):
        bpy.ops.object.game_property_new(name='w'+str(j))
    
    #adds mblur 2d filter
    if 'mblur.glsl' not in bpy.data.texts:
        set_path = os.path.join(directory,'filters','mblur.txt')
        text = bpy.data.texts.load(set_path)
    
        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                ctx = bpy.context.copy()
                ctx['edit_text'] = text
                
                area.spaces[0].text = bpy.data.texts['mblur.txt']  
                break
        bpy.data.texts['mblur.txt'].name = 'mblur.glsl'
    if 'mblur_camerainfo.py' not in bpy.data.texts:
        new_path = os.path.join(directory, 'filters', 'mblur_camerainfo.txt')
        text = bpy.data.texts.load(new_path)
        bpy.data.texts['mblur_camerainfo.txt'].name = 'mblur_camerainfo.py'
    
    #adding logic
    current = bpy.context.active_object
    bpy.ops.logic.sensor_add(type='ALWAYS', name='get_info',object='Mblur_empty')
    bpy.ops.logic.controller_add(type='PYTHON',object='Mblur_empty')
    link_sensor = current.game.sensors[-1]
    link_controller = current.game.controllers[-1]
    link_sensor.use_pulse_true_level = True
    link_sensor.show_expanded = False
    link_controller.text = bpy.data.texts['mblur_camerainfo.py']
    link_controller.show_expanded = False
    link_sensor.link(link_controller)  
    
    #adding 2d filter
    bpy.ops.logic.sensor_add(type='ALWAYS', name='filter_always',object='Mblur_empty')
    bpy.ops.logic.controller_add(type='LOGIC_AND',object='Mblur_empty')
    filter_sensor = current.game.sensors[-1]
    filter_controller = current.game.controllers[-1]
    filter_sensor.show_expanded = False
    filter_controller.show_expanded = False
    filter_sensor.link(filter_controller)
    bpy.ops.logic.actuator_add(type='FILTER_2D',name='mblur', object='Mblur_empty')
    added = current.game.actuators[-1]
        
    added.mode = 'CUSTOMFILTER'
    added.filter_pass = pass_num
    added.glsl_shader = bpy.data.texts['mblur.glsl']
    added.show_expanded = False
    added.link(filter_controller)
    for i in bpy.context.scene.objects:
        i.select = False
    bpy.context.scene.objects.active = bpy.data.objects[used_camera.name]
    bpy.context.scene.objects[used_camera.name].select = True

#add the correct filter with logic
def addFilter(new_filter,directory,pass_num):
    
    current = bpy.context.selected_objects[0]
    
    prop_dict = {'D.O.F.': [('focalLength','FLOAT',29.0),('fstop', 'FLOAT',15.0)], 'S.S.A.O.': [], 'BLOOM':[('bloom_amount', 'FLOAT', 0.5)], 'NOISE':[('noise_amount','FLOAT',-0.1),('timer','TIMER',0.0)], 'VIGNETTE':[('vignette_size','FLOAT',0.7)], 'RETINEX':[('retinex','FLOAT',-1.2)], 'CHROMATIC ABERRATION':[('abberation', 'FLOAT', 0.82)],'WATER':[('timer','TIMER',0.0)],'BLOOM X':[('bloom_x', 'FLOAT', 0.4)],'BLEACH':[('bleach_amount', 'FLOAT', 1.0)], 'BARREL':[], 'F.X.A.A.':[],'GAMEBOY COLOR':[],'LEVELS':[], 'NIGHT VISION':[('vision_strength','FLOAT', 7.0)], 'RADIAL BLUR':[('radial_density', 'FLOAT', 0.05)], 'TOON':[('line_size','FLOAT',0.6)], 'H.D.R.':[('avgL','FLOAT',0.0), ('HDRamount','FLOAT',0.1)], 'GAMMA':[]}
    
    property_list = prop_dict[new_filter]
    if '.' in new_filter:
        new_filter = derive_name(new_filter)
        
    filter_name = new_filter +'.txt'
    
    if new_filter+'.glsl' not in bpy.data.texts:
        set_path = os.path.join(directory,'filters',filter_name)
        text = bpy.data.texts.load(set_path)
    
        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                ctx = bpy.context.copy()
                ctx['edit_text'] = text
                
                area.spaces[0].text = bpy.data.texts[new_filter + '.txt']                
                break
        bpy.data.texts[new_filter +'.txt'].name = new_filter +'.glsl'
        
    #additional scripts for HDR
    if new_filter == 'HDR':
        if 'ReadLum.py' not in bpy.data.texts:
            new_path = os.path.join(directory, 'filters', 'ReadLum.txt')
            text = bpy.data.texts.load(new_path)
            bpy.data.texts['ReadLum.txt'].name = 'ReadLum.py'
        bpy.ops.logic.sensor_add(type='ALWAYS', name='check_lum',object=current.name)
        bpy.ops.logic.controller_add(type='PYTHON',object=current.name)
        link_sensor = current.game.sensors[-1]
        link_controller = current.game.controllers[-1]
        link_sensor.use_pulse_true_level = True
        link_sensor.show_expanded = False
        link_controller.text = bpy.data.texts['ReadLum.py']
        link_controller.show_expanded = False
        link_sensor.link(link_controller)        
    #check for current always sensor if non existant add a new one
    if 'filter_always' not in current.game.sensors:
        bpy.ops.logic.sensor_add(type='ALWAYS', name='filter_always',object=current.name)
        bpy.ops.logic.controller_add(type='LOGIC_AND',object=current.name)
        link_sensor = current.game.sensors[-1]
        link_controller = current.game.controllers[-1]
        link_sensor.show_expanded = False
        link_controller.show_expanded = False
        link_sensor.link(link_controller)

    sensor = current.game.sensors['filter_always']
    controller = sensor.controllers[0]
    
    bpy.ops.logic.actuator_add(type='FILTER_2D',name=new_filter, object=current.name)
    added = current.game.actuators[-1]
    
    added.mode = 'CUSTOMFILTER'
    added.filter_pass = pass_num
    added.glsl_shader = bpy.data.texts[new_filter +'.glsl']
    
    added.link(controller)
    
    if len(property_list) > 0:
        for prop in property_list:
            if prop[0] not in current.game.properties:
                bpy.ops.object.game_property_new(type=prop[1],name=prop[0])
                current.game.properties[prop[0]].value = prop[2]

def removeFilter(selected_filter):
    if selected_filter != 'MOTION BLUR':
        
        if '.' in selected_filter:
            selected_filter = derive_name(selected_filter)     
        current = bpy.context.selected_objects[0]
        
        filters_used = []
        
        for i in bpy.data.cameras:
            if i.name in bpy.context.scene.objects.keys():
                current = bpy.context.scene.objects[i.name]
                for j in current.game.actuators:
                    if j.type == 'FILTER_2D' and j.mode == "CUSTOMFILTER" and j.glsl_shader != None:
                        filters_used.append(j.glsl_shader.name)
        current = bpy.context.selected_objects[0]
        #remove logic
        sensor1 = current.game.sensors['filter_always']
        controller1 = sensor1.controllers[0]
        if len(controller1.actuators) < 2:
            bpy.ops.logic.sensor_remove(sensor=sensor1.name, object=current.name)
            bpy.ops.logic.controller_remove(controller=controller1.name, object=current.name)
        bpy.ops.logic.actuator_remove(actuator=selected_filter, object=current.name)
        
        #remove properties
        prop_dict = {'DOF': ['focalLength','fstop'], 'SSAO': [], 'BLOOM':['bloom_amount'], 'NOISE':['noise_amount','timer'], 'VIGNETTE':['vignette_size'], 'RETINEX':['retinex'],'WATER':['timer'], 'CHROMATIC ABERRATION':['abberation'], 'BLOOM X':['bloom_x'], 'BLEACH':['bleach_amount'], 'BARREL':[], 'FXAA':[], 'GAMEBOY COLOR':[], 'LEVELS':[], 'NIGHT VISION':['vision_strength'], 'RADIAL BLUR':['radial_density'],'TOON':['line_size'], 'HDR':['avgL', 'HDRamount'], 'GAMMA':[]}
        
        timer_props = ['NOISE.glsl','WATER.glsl']
        remove_list = prop_dict[selected_filter]
        
        
        for prop in remove_list:
            for each in range(len(current.game.properties)):
                #checks if property is the correct one.
                if current.game.properties[each].name == prop:
                    
                    if prop == 'timer':
                        #removes the current filter
                        timer_props.remove(selected_filter+'.glsl')
                        remove_timer = True
                        for i in timer_props:
                            if i in filters_used:
                                remove_timer = False
                                break
                        if remove_timer == True:                
                            bpy.ops.object.game_property_remove(index=each)
                            break
                        else:
                            break
                    else:
                        bpy.ops.object.game_property_remove(index=each)
                        break
        bpy.data.texts.remove(bpy.data.texts[selected_filter +'.glsl'], do_unlink=True)
    else:
        used_camera = bpy.context.active_object
        for ob in bpy.context.scene.objects:
            ob.select = ob.name == 'Mblur_empty'
        bpy.ops.object.delete()
        bpy.data.texts.remove(bpy.data.texts['mblur.glsl'], do_unlink=True)
        bpy.data.texts.remove(bpy.data.texts['mblur_camerainfo.py'], do_unlink=True)
        for i in bpy.context.scene.objects:
                i.select = False
        bpy.context.scene.objects.active = bpy.data.objects[used_camera.name]
        bpy.context.scene.objects[used_camera.name].select = True        
        
    #reassign passes
    
    filters_used = []
    
    scn = bpy.context.scene
    
    for i in scn.objects:
        if i.type == 'CAMERA':
            current = bpy.context.scene.objects[i.name]
            for j in current.game.actuators:
                if j.type == 'FILTER_2D' and j.mode == 'CUSTOMFILTER' and j.glsl_shader != None:
                    filters_used.append(j.glsl_shader.name)
    if 'Mblur_empty' in bpy.context.scene.objects:
        filters_used.append('Mblur_empty')
    if len(filters_used) == 0:
        scn.index_num = 0
    
    #removing HDr logic
    if selected_filter == 'HDR':
        #remove logic
        sensor1 = current.game.sensors['check_lum']
        controller1 = sensor1.controllers[0]
        bpy.ops.logic.sensor_remove(sensor=sensor1.name, object=current.name)
        bpy.ops.logic.controller_remove(controller=controller1.name, object=current.name)
        bpy.data.texts.remove(bpy.data.texts['ReadLum.py'])

def check_mblur_remove():
    return 'Mblur_empty' in bpy.context.scene.objects
    
def check_filters(filter_tocheck):
    
    if '.' in filter_tocheck:
        selected = derive_name(filter_tocheck)     
    else:
        selected = filter_tocheck
    
    for i in bpy.context.scene.objects:
        current = bpy.context.scene.objects[i.name]
        for j in current.game.actuators:
            if j.type == 'FILTER_2D' and j.mode == 'CUSTOMFILTER' and j.glsl_shader != None:
                if selected +'.glsl' == j.glsl_shader.name:
                    return True
    return False


def check_remove(filter_tocheck):
    
    if '.' in filter_tocheck:
        chosen = derive_name(filter_tocheck)
    else:
        chosen = filter_tocheck
    #check that the desired filter is on selected object
    for i in bpy.context.selected_objects[0].game.actuators:
        if i.type == 'FILTER_2D' and i.mode == 'CUSTOMFILTER' and i.glsl_shader != None:
            if chosen+'.glsl' == i.glsl_shader.name:
                return True
    return False

def derive_name(name):
    new_name = ''
    for letter in name:
        if letter != '.':
            new_name += letter
    return new_name
  

def register():
    bpy.types.Scene.index_num = IntProperty(default = 0)
    bpy.types.Scene.Chosen_filter = EnumProperty(items = [('H.D.R.','H.D.R.','Adjusts light levels to suit environment'), ('GAMMA','GAMMA', 'Brightens dark spaces'), ('GAMEBOY COLOR','GAMEBOY COLOR', 'Gameboy style pixelization.'),('F.X.A.A.','F.X.A.A.','Efficient Anti-Aliasing'), ('D.O.F.','D.O.F.','Adds depth of field'),('CHROMATIC ABERRATION','CHROMATIC ABERRATION','Coloured Fringing'), ('BLOOM X','BLOOM X', 'Adds X shaped glow to objects'),('BLOOM','BLOOM', 'Adds glow to bright objects'), ('BLEACH', 'BLEACH', 'Horror game filter. Low saturation, high contrast.'),('BARREL', 'BARREL', 'Adds buldge distortion to the centre of the screen'), ('WATER','WATER','Underwater distortion effect'),('VIGNETTE','VIGNETTE', 'Darkens the edges of the screen'),('TOON','TOON','Adds toon outline'),('S.S.A.O.','S.S.A.O.', 'Darkens edges of objects'),('RETINEX','RETINEX','Enhances contrast, maintains color.'),('RADIAL BLUR', 'RADIAL BLUR', 'Adds blur around the edges of the screen'),('NOISE','NOISE','Adds noise to the screen'), ('NIGHT VISION', 'NIGHT VISION', 'Infared style night vision'), ('MOTION BLUR', 'MOTION BLUR', 'Adds Motion Blur'), ('LEVELS','LEVELS', 'Color channel remapping with curves')],name = "Choose Filter", default='D.O.F.')
    bpy.utils.register_module(__name__)
    

def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.index_num
    del bpy.types.Scene.Chosen_filter