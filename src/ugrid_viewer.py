"""
design notes -

would like to have something visit-ish, but more pythonic.
well, another day.
"""
import sys

import numpy as np

import netCDF4
from tvtk.api import tvtk
from mayavi import mlab

from  ugrid import Ugrid

# quick and dirty plotting for cf-convention, unstructured data
# makes a lot of assumptions, but for the nc files generated by test_nc.py
# it at least shows reasonable bathymetry and salinity fields - and 
# pretty fast, too.

        

class UgridViewer(Ugrid):
    def twod_mesh_polydata(self,mesh_name):
        """
        Given name of mesh topology variable, extract nodes
        and faces, put together in a tvtk PolyData object.
        """
        mesh_var = self.nc.variables[mesh_name]

        ## The TVTK dataset:
        points3D = self.get_node_array(mesh_var.node_coordinates)

        # for now, don't worry about fill values here - for suntans
        # it's always full, always 3.
        faces = self.nc.variables[mesh_var.face_node_connectivity][:,:]

        polydata = tvtk.PolyData(points=points3D, polys=faces)
        return polydata
    
    def twod_mesh_linedata(self,mesh_name):
        """ Return a polydata where each 'cell' is an edge 
        """
        mesh_var = self.nc.variables[mesh_name]

        ## The TVTK dataset:
        points3D = self.get_node_array(mesh_var.node_coordinates)

        # for now, don't worry about fill values here - for suntans
        # it's always full, always 3.
        edges = self.nc.variables[mesh_var.edge_node_connectivity][:,:]

        polydata = tvtk.PolyData(points=points3D, lines=edges)
        return polydata
    

### related, but non-ugrid, functions
def tg_cell_polydata(g,z_mode='flat',z_data=0.0):
    """
    Create a tvtk PolyData for the cells of the grid
    z_mode: 'flat' -> z coordinate of points set to 0.
            'node' -> z_data is z elevations for each node
            'cell' -> z_data is z elevations for each cell

    currently, flat and nodes are treated the same, and the
      dimension of z_data controls what happens.
    """
    if z_mode in ('flat','node'):
        points3d = np.zeros( (g.Npoints(),3), np.float64)
        points3d[:,:2] = g.points
        points3d[:,2] = z_data # may be scalar or array
        polydata = tvtk.PolyData(points=points3d, polys=g.cells)
    else: # 'cell'
        points3d = np.zeros( (g.Ncells(),3,3), np.float64) # [cell,node,xyz]
        points3d[:,:,:2] = g.points[g.cells]
        points3d[:,:,2] = z_data[:,None]
        points3d = points3d.reshape([-1,3])
        polydata = tvtk.PolyData(points=points3d,
                                 polys=np.arange(3*g.Ncells()).reshape([-1,3]))
    return polydata

def tg_edge_polydata(g,z_mode='flat',z_data=0.0):
    """ Create a tvtk Polydata for the edges of the grid
    z_mode: 'flat' / 'node' - elevation of the nodesz_data
      are assigned from z_data.
      'edge' - each edge gets a constant elevation, given by z_data
    """
    if z_mode in ('flat','node'):
        points3d = np.zeros( (g.Npoints(),3), np.float64)
        points3d[:,:2] = g.points
        points3d[:,2] = z_data # may be scalar or array
        polydata = tvtk.PolyData(points=points3d, lines=g.edges[:,:2])
    else: # 'cell'
        points3d = np.zeros( (g.Nedges(),2,3), np.float64) # [edge,node,xyz]
        points3d[:,:,:2] = g.points[g.edges[:,:2]]
        points3d[:,:,2] = z_data[:,None]
        points3d = points3d.reshape([-1,3])
        polydata = tvtk.PolyData(points=points3d,
                                 lines=np.arange(2*g.Nedges()).reshape([-1,2]))
    return polydata

        
if __name__ == '__main__':
    uv = UgridViewer(sys.argv[1])

    fig = mlab.gcf()
    for mesh_name in uv.mesh_names():
        pdata = uv.twod_mesh_polydata(mesh_name)
        mapper = tvtk.PolyDataMapper(input=pdata)
        actor = tvtk.Actor(mapper=mapper)
        fig.scene.add_actor(actor)


        if 0:
            # assign a cell-centered scalar - depth?
            pdata.cell_data.scalars =  uv.nc.variables[mesh_name+'_depth'][:]
            mapper.scalar_range=[3,20]
        else:
            # or salinity? should be [cell,zlevel,time]
            pdata.cell_data.scalars = uv.nc.variables[mesh_name+'_salinity'][:,0,0]
            mapper.scalar_range=[10,35]

    # sometimes the plots don't auto-update.
    mlab.draw()

    from pyface.api import GUI
    gui = GUI()
    gui.start_event_loop()



