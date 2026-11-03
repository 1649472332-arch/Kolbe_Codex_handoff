"""FreeCAD BRep + native PartDesign helpers. Run with FreeCAD's bundled Python."""
import json, math
from pathlib import Path
import FreeCAD as App
import Part, Sketcher
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/'design_basis.json').read_text(encoding='utf-8'))
V=App.Vector

def doc_new(name):
    if name in App.listDocuments(): App.closeDocument(name)
    return App.newDocument(name)

def body_new(doc,name,label=None):
    b=doc.addObject('PartDesign::Body',name);b.Label=label or name
    b.addProperty('App::PropertyString','DesignStatus','Design');b.DesignStatus=P['status']
    return b

def sketch(body,name,geometry,placement=None):
    s=body.newObject('Sketcher::SketchObject',name)
    if placement: s.Placement=placement
    for g in geometry:
        idx=s.addGeometry(g,False)
        # Block constraint keeps each source dimension exact and editable in sketch.
        # All design-driving dimensions remain in design_basis.json for regeneration.
        try:s.addConstraint(Sketcher.Constraint('Block',idx))
        except Exception:pass
    s.Visibility=False
    return s

def poly(points):
    return [Part.LineSegment(V(points[i][0],points[i][1],0),V(points[(i+1)%len(points)][0],points[(i+1)%len(points)][1],0)) for i in range(len(points))]

def rect(x1,y1,x2,y2):return poly([(x1,y1),(x2,y1),(x2,y2),(x1,y2)])

def rounded(w,h,r,cx=0,cy=0):
    x=w/2;y=h/2
    geo=[Part.LineSegment(V(cx-x+r,cy-y,0),V(cx+x-r,cy-y,0)),
         Part.ArcOfCircle(Part.Circle(V(cx+x-r,cy-y+r,0),V(0,0,1),r),-math.pi/2,0),
         Part.LineSegment(V(cx+x,cy-y+r,0),V(cx+x,cy+y-r,0)),
         Part.ArcOfCircle(Part.Circle(V(cx+x-r,cy+y-r,0),V(0,0,1),r),0,math.pi/2),
         Part.LineSegment(V(cx+x-r,cy+y,0),V(cx-x+r,cy+y,0)),
         Part.ArcOfCircle(Part.Circle(V(cx-x+r,cy+y-r,0),V(0,0,1),r),math.pi/2,math.pi),
         Part.LineSegment(V(cx-x,cy+y-r,0),V(cx-x,cy-y+r,0)),
         Part.ArcOfCircle(Part.Circle(V(cx-x+r,cy-y+r,0),V(0,0,1),r),math.pi,math.pi*1.5)]
    return geo

def circle(x,y,r):return Part.Circle(V(x,y,0),V(0,0,1),r)

def at_z(z):return App.Placement(V(0,0,z),App.Rotation())

def pad(body,name,profile,length,reversed=False):
    f=body.newObject('PartDesign::Pad',name);f.Profile=profile;f.Length=length;f.Reversed=reversed
    body.Document.recompute();profile.Visibility=False
    if f.BaseFeature:f.BaseFeature.Visibility=False
    return f

def pocket(body,name,profile,length,reversed=False):
    f=body.newObject('PartDesign::Pocket',name);f.Profile=profile;f.Length=length;f.Reversed=reversed
    body.Document.recompute();profile.Visibility=False
    if f.BaseFeature:f.BaseFeature.Visibility=False
    return f

def feature(body,name,shape,**props):
    f=body.newObject('PartDesign::Feature',name);f.Shape=shape
    for key,value in props.items():
        f.addProperty('App::PropertyString',key,'Specification');setattr(f,key,str(value))
    for ob in body.Group:
        if ob!=f:ob.Visibility=False
    body.Tip=f;return f

def finish(doc,body,code,material,color=(.75,.75,.75)):
    doc.recompute();body.Label=code+' | '+body.Label
    body.addProperty('App::PropertyString','PartNumber','Design');body.PartNumber=code
    body.addProperty('App::PropertyString','MaterialSpecification','Design');body.MaterialSpecification=material
    s=body.Shape
    if not s.isValid() or len(s.Solids)!=1 or s.Volume<=0:raise ValueError('Invalid solid '+code)
    if App.GuiUp:body.ViewObject.ShapeColor=color;body.Tip.ViewObject.ShapeColor=color
    from chinese_names import localize_document
    localize_document(doc)
    doc.recompute();doc.saveAs(str(ROOT/'parts'/(code+'.FCStd')))
    Part.export([body],str(ROOT/'parts'/(code+'.step')))
    return {'code':code,'file':code+'.FCStd','volume_mm3':s.Volume,'valid':s.isValid(),'solids':len(s.Solids),'features':len(body.Group),'material':material}
