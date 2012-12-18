#Circles
#Rolph Recto

import wx
import matplotlib as mpl
mpl.use('WXAgg')
import matplotlib.patches as patches
import matplotlib.backends.backend_wxagg as mpl_wx
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from math import *

#utility functions
def isnumeric(a):
    try:
        float(a)
        return True
    except ValueError:
        return False

#figure parameter was changed
#circle was dilated or translated
class FigureTransformEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.oldH, self.oldR, self.oldR = 0, 0, 0
        self.deltaH, self.deltaK, self.deltaR = 0, 0, 0
        self.newH, self.newK, self.newR = 0, 0, 0

#set up new event type
typeEVT_FIGURE_DILATE = wx.NewEventType()
EVT_FIGURE_DILATE = wx.PyEventBinder(typeEVT_FIGURE_DILATE, 1)
typeEVT_FIGURE_TRANSLATE = wx.NewEventType()
EVT_FIGURE_TRANSLATE = wx.PyEventBinder(typeEVT_FIGURE_TRANSLATE, 1)

class CircleToolbar(NavigationToolbar):
    TOOL_HOME = wx.NewId()
    TOOL_PAN = wx.NewId()
    TOOL_ZOOM_IN = wx.NewId()
    TOOL_ZOOM_OUT = wx.NewId()
    TOOL_SET_WINDOW = wx.NewId()

    def __init__(self, canvas):
        NavigationToolbar.__init__(self, canvas)
        #remove all tools
        self.ClearTools()
        self.SetToolBitmapSize(wx.Size(24,24))
        artProvider = wx.ArtProvider()
        self.AddSimpleTool(self.TOOL_HOME, artProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR),
            'Home', 'Reset window to default')
        self.AddSimpleTool(self.TOOL_PAN, artProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_TOOLBAR),
            'Home', 'Reset window to default')
        self.AddSimpleTool(self.TOOL_ZOOM_OUT, artProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_TOOLBAR),
            'Home', 'Reset window to default')
        self.AddSimpleTool(self.TOOL_ZOOM_IN, artProvider.GetBitmap(wx.ART_GO_UP, wx.ART_TOOLBAR),
            'Home', 'Reset window to default')
        self.AddSimpleTool(self.TOOL_SET_WINDOW, artProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_TOOLBAR),
            'Home', 'Reset window to default')

        self.Realize()

#panel that contains the actual plotting canvas
class CirclePanel(wx.Panel):
    def __init__(self, parent, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        #set up widgets
        self.figure = Figure((5, 5), 80)
        self.figure.set_facecolor("#FFFFFF")
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.canvas.SetBackgroundColour(wx.Colour(255,255,255))
        self.subplot = self.figure.add_subplot(111)
        self.subplot.set_ylim([-5, 5])
        self.subplot.set_xlim([-5, 5])
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.SetBackgroundColour(wx.Colour(255, 255, 255))

        #set up boxes
        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.canvas, 1, wx.LEFT | wx.GROW) #the sizer automatically resizes the canvas
        self.box.Add(self.toolbar, 0, wx.CENTER)
        self.SetSizer(self.box)

        #set up the point dragging feature;
        #user can drag center and move circle
        self.canvas.mpl_connect("pick_event", self.OnPick)
        self.canvas.mpl_connect("motion_notify_event", self.OnMotion)
        self.canvas.mpl_connect("button_release_event", self.OnMouseUp)
        self.dragging = False

        #circle parameters
        self.h = 0.0
        self.k = 0.0
        self.r = 1.0

        #plot objects
        self.background = None
        self.circle = None
        self.points = None

        self.DrawFigure()

    #user picked a point/line in the plot
    def OnPick(self, event):
        #the user picked more than one point because
        #there is a point on top of another;
        #just pick the first point
        if not isinstance(event.ind, type(1)):
            event.ind = event.ind[0]

        #if the user picked the center point, enable translation
        #the center point is the first point of the point list (ind=0)
        if event.ind == 0:
            self.dragging = 1
            self.SaveBackground()
        #if the user picked the diameter point, enable dilation
        #the diameter point is the second point of the point list (ind=1)
        elif event.ind == 1:
            self.dragging = 2
            self.SaveBackground()

    #user moved the mouse in the plot
    def OnMotion(self, event):
        #make sure that the mouse is IN the plot!
        if not event.xdata == None:
            #if user is dragging the center point,
            #move the center point to mouse coordinates
            if self.dragging == 1:
                evt = FigureTransformEvent(typeEVT_FIGURE_TRANSLATE, self.GetId())
                evt.oldH = self.h
                evt.oldK = self.k
                evt.oldR = self.r
                evt.deltaH = self.h - event.xdata
                evt.deltaK = self.k - event.ydata
                self.h = event.xdata
                self.k = event.ydata
                evt.newH = self.h
                evt.newK = self.k
                self.UpdateFigure()
                self.GetEventHandler().ProcessEvent(evt)
            #if user is dragging the diameter point,
            #change the radius to the distance between the diameter and center point
            if self.dragging == 2:
                evt = FigureTransformEvent(typeEVT_FIGURE_DILATE, self.GetId())
                #make sure r is greater than 0
                if event.xdata - self.h > 0.0:
                    evt.oldH = self.h
                    evt.oldK = self.k
                    evt.oldR = self.r
                    self.r = event.xdata - self.h
                    evt.deltaR = evt.oldR - self.r
                    evt.newR = self.r
                    self.UpdateFigure()
                    self.GetEventHandler().ProcessEvent(evt)

    #user released button
    def OnMouseUp(self, event):
        #if the user is dragging the center point
        #and releases the button, stop dragging
        self.dragging = 0
        self.circle.set_animated(False)
        self.points.set_animated(False)

    #update the title, which shows the equation of the circle
    def UpdateTitle(self):
        titleText = "$(x{h})^2 + (y{k})^2 = {r}^2$"
        titleH, titleK, titleR = "-0.0", "-0.0", round(self.r, 2)

        #format signs correctly
        if self.h < 0.0:
            titleH = "+{val}".format(val=abs(round(self.h, 2)))
        elif self.h > 0.0:
            titleH = "-{val}".format(val=abs(round(self.h, 2)))
        if self.k < 0.0:
            titleK = "+{val}".format(val=abs(round(self.k, 2)))
        elif self.k > 0.0:
            titleK = "-{val}".format(val=abs(round(self.k, 2)))

        #show the students that they can omit h or k in the equation if it equals 0.0
        if self.h == 0.0 and not self.k == 0.0:
            titleText = titleText + " OR $x^2 + (y{k})^2 = {r}^2$"
        elif not self.h == 0.0 and self.k == 0.0:
            titleText = titleText + " OR $(x{h})^2 + y^2 = {r}^2$"
        elif self.h == 0.0 and self.k == 0.0:
            titleText = titleText + " OR $x^2 + y^2 = {r}^2$"

        self.subplot.set_title(titleText.format(h=titleH, k=titleK, r=titleR),
            fontproperties=mpl.font_manager.FontProperties(size="x-large"))

    #draw/redraw the canvas
    def DrawFigure(self):
        self.subplot.clear()

        #set the "window" of the plot
        self.subplot.set_ylim([-5, 5])
        self.subplot.set_xlim([-5, 5])

        #draw grid and axes lines
        self.subplot.grid(True)
        self.subplot.axhspan(0, 0)
        self.subplot.axvspan(0, 0)

        self.UpdateTitle()

        #draw the circles
        circleColor = (0, 0, 1, 1)
        #must multiply r by 2 b/c Arc takes the length (diameter) of the axes, not the radius

        #circle1 is the reference circle (red)
        """
        circle1 = patches.Arc((0, 0), 2, 2, edgecolor="#FF0000", alpha=0.8)
        self.subplot.plot([0.0, 1.0], [0.0, 0.0], marker="o", color="#FF0000", mec="#FF0000", mfc="#FF0000")
        self.subplot.add_patch(circle1)
        """

        #circle2 is the user-manipulated circle (blue)
        self.circle = patches.Arc((self.h, self.k), self.r*2, self.r*2, edgecolor=circleColor, alpha=0.8)
        self.points = self.subplot.plot([self.h, self.h+self.r], [self.k, self.k], marker="o", picker=5, color=circleColor, mec=circleColor, mfc=circleColor)
        #get the first (and only) line, not the list
        self.points = self.points[0]
        self.subplot.add_patch(self.circle)

        self.canvas.draw()

    def UpdateFigure(self):
        #update data
        self.circle.center = (self.h, self.k)
        self.circle.width = 2*self.r
        self.circle.height = 2*self.r
        self.points.set_xdata([self.h, self.h+self.r])
        self.points.set_ydata([self.k, self.k])
        self.UpdateTitle()

        #draw
        self.canvas.restore_region(self.background)
        self.subplot.draw_artist(self.subplot.title)
        self.subplot.draw_artist(self.circle)
        self.subplot.draw_artist(self.points)
        self.canvas.blit(self.figure.bbox)

    def SaveBackground(self):
        self.circle.set_animated(True)
        self.points.set_animated(True)

        #clear plot
        self.subplot.set_title(" ")
        self.canvas.draw()

        #save figure
        self.background = self.canvas.copy_from_bbox(self.figure.bbox)

        self.UpdateTitle()

        #blit figures back onto the plot
        self.subplot.draw_artist(self.circle)
        self.subplot.draw_artist(self.points)
        self.subplot.draw_artist(self.subplot.title)
        self.canvas.blit(self.figure.bbox)

    def SetParameters(self, h, k, r):
        self.h = h
        self.k = k
        self.r = r


#frame (window) that contains canvas and a control panel
class CircleFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.SetMinSize((525, 600))
        self.SetSize((525, 600))

        #create status bar that will display graph coordinates
        self.statusBar = self.CreateStatusBar()
        self.statusBar.SetLabel("Hello!")

        #set top-level sizer
        self.boxTop = wx.BoxSizer(wx.VERTICAL)

        #set up plot panel
        self.panelCircle = CirclePanel(self)

        #set up control panel
        self.panelControl = wx.Panel(self)
        self.labelH = wx.StaticText(self.panelControl, -1, "h: ")
        self.textH = wx.TextCtrl(self.panelControl, -1, "0")
        self.labelK = wx.StaticText(self.panelControl, -1, "k: ")
        self.textK = wx.TextCtrl(self.panelControl, -1, "0")
        self.labelR = wx.StaticText(self.panelControl, -1, "r: ")
        self.textR = wx.TextCtrl(self.panelControl, -1, "1")
        self.buttonPlot = wx.Button(self.panelControl, -1, "Plot")

        #set up control panel sizer
        #adds horizontal margins to control panel
        self.boxControlSpacer = wx.BoxSizer(wx.VERTICAL)
        #contains actual control panel widgets
        self.boxControl = wx.BoxSizer(wx.HORIZONTAL)

        self.boxControlSpacer.AddSpacer(20)
        self.boxControlSpacer.Add(self.boxControl, 1, wx.EXPAND)
        self.boxControlSpacer.AddSpacer(20)

        self.boxControl.AddSpacer(20)
        self.boxControl.Add(self.labelH, 0)
        self.boxControl.AddSpacer(5)
        self.boxControl.Add(self.textH, 0)
        self.boxControl.AddSpacer(20)
        self.boxControl.Add(self.labelK, 0)
        self.boxControl.AddSpacer(5)
        self.boxControl.Add(self.textK, 0)
        self.boxControl.AddSpacer(20)
        self.boxControl.Add(self.labelR, 0)
        self.boxControl.AddSpacer(5)
        self.boxControl.Add(self.textR, 0)
        self.boxControl.AddSpacer(20)
        self.boxControl.Add(self.buttonPlot, 0)
        self.boxControl.AddSpacer(20)

        self.panelControl.SetSizer(self.boxControlSpacer)

        #setup the top-level sizer
        self.boxTop.Add(self.panelCircle, 1, wx.EXPAND)
        self.boxTop.Add(self.panelControl, 0, wx.CENTER)
        self.SetSizer(self.boxTop)

        #bind event handlers
        self.Bind(wx.EVT_BUTTON, self.OnPlot, self.buttonPlot)
        self.panelCircle.canvas.mpl_connect('motion_notify_event', self.OnCanvasMotion)
        self.Bind(EVT_FIGURE_DILATE, self.OnCircleDilate, self.panelCircle)
        self.Bind(EVT_FIGURE_TRANSLATE, self.OnCircleTranslate, self.panelCircle)

    #plot button pressed; redraw plot with new parameters
    def OnPlot(self, event):
        h = self.textH.GetLabelText()
        k = self.textK.GetLabelText()
        r = self.textR.GetLabelText()
        if isnumeric(h) and isnumeric(k) and isnumeric(r):
            h = float(self.textH.GetLabelText())
            k = float(self.textK.GetLabelText())
            r = float(self.textR.GetLabelText())
            self.panelCircle.SetParameters(h, k, r)
            self.panelCircle.DrawFigure()
        else:
            self.ParameterError("The values of h, k, and r must be numbers!")

    #mouse moved in canvas; change plot coordinates in statusBar
    def OnCanvasMotion(self, event):
        #mouse is inside of plot
        if not event.xdata == None:
            xCoord = round(float(event.xdata),2)
            yCoord = round(float(event.ydata),2)
            statusText = "({x}, {y})".format(x=xCoord, y=yCoord)
            self.statusBar.SetLabel(statusText)
        #mouse is outside of plot
        else:
            self.statusBar.SetLabel("")

    #user moved the circle around (dragged center point)
    def OnCircleTranslate(self, event):
        self.textH.SetLabel(str(round(event.newH, 2)))
        self.textK.SetLabel(str(round(event.newK, 2)))
        self.textH.Refresh()
        self.textK.Refresh()

    def ParameterError(self, msg):
        dialog = wx.MessageDialog(None, msg, "Parameter Error", wx.OK | wx.ICON_EXCLAMATION)
        dialog.ShowModal()
        dialog.Destroy()

    #user changed the circle radius (dragged diameter point)
    def OnCircleDilate(self, event):
        self.textR.SetLabel(str(round(event.newR, 2)))
        self.textR.Refresh()

class CircleApp(wx.App):
    def OnInit(self):
        self.frame = CircleFrame(None, "   ")
        self.frame.Show()
        self.SetTopWindow(self.frame)

        return True

if __name__ == '__main__':
    app = CircleApp()
    app.MainLoop()