"""Tianlai dish and cylinder array."""

import numpy as np
import aipy as ap

import constants as const


def xyz2XYZ_m(lat):
    """Conversion matrix through xyz to XYZ.

    xyz coord: z toward zenith, x toward East, y toward North, xy in the horizon plane;
    XYZ coord: Z toward north pole, X in the local meridian plane, Y toward East, XY plane parallel to equatorial plane.

    Parameters
    ----------
    lat : float
        Latitude of the observing position in radians.

    """
    sin_a, cos_a = np.sin(lat), np.cos(lat)
    zero = np.zeros_like(lat)
    one = np.ones_like(lat)
    mat =  np.array([[  zero,   -sin_a,   cos_a  ],
                     [   one,     zero,    zero  ],
                     [  zero,    cos_a,   sin_a  ]])
    if len(mat.shape) == 3:
        mat = mat.transpose([2, 0, 1])

    return mat


class DishBeam(ap.fit.Beam2DGaussian):
    """Circular beam of a dish antenna."""

    def __init__(self, freqs, diameter=6.0):
        """Initialize the beam.

        Parameters
        ----------
        freqs : array like
            Frequencies in MHz.
        diameter : float, optional
            Diameter of the dish in m. Default is 6.0.

        """

        freqs = 1.0e-3 * np.array([freqs])  # in GHz
        lmbda = const.c / (1.0e9 * freqs) # in m
        xwidth = 1.22 * lmbda / diameter
        ywidth = xwidth
        ap.fit.Beam2DGaussian.__init__(self, freqs, xwidth, ywidth)


class CylinderBeam(ap.fit.Beam):
    """Beam of a cylinder feed."""

    def __init__(self, freqs, width=15.0, length=40.0):
        """Initialize the beam.

        Parameters
        ----------
        freqs : array like
            Frequencies in MHz.
        width : float, optional
            Cylinder width. Default is 15.0.
        length : float, optional
            Cylinder length. Default is 40.0.

        """

        freqs = 1.0e-3 * np.array([freqs])  # in GHz
        ap.fit.Beam.__init__(self, freqs)
        self.width = width
        self.length = length

    def response(self, xyz):
        """Beam response across active band for specified topocentric coordinates.

        This is just a simple beam model as the product of 2 sinc function.

        Parameters
        ----------
        xyz : array like, of shape (3, ...)
            Unit direction vector in topocentric coordinates (x=E, y=N, z=UP).
            `xyz` may be arrays of multiple coordinates.


        Returns
        -------
        Returns 'x' linear polarization (rotate pi/2 for 'y') of shape (nfreq, ...).

        """

        vec_n = np.array(xyz).T
        vec_z = np.array([0.0, 0.0, 1.0]) # unit vector pointing to the zenith
        nz = np.dot(vec_n, vec_z)

        vec_u = np.array([1.0, 0.0, 0.0]) # unit vector pointing East in the ground-plane
        vec_v = np.array([0.0, 1.0, 0.0]) # unit vector pointing North in the ground-plane
        nu = np.dot(vec_n, vec_u)
        nv = np.dot(vec_n, vec_v)

        shp = tuple([-1] + [1] * len(nz.shape))
        lmbda = const.c / (1.0e9 * self.freqs).reshape(shp) # in m

        nz = np.where(nz<=0.0, 0.0, nz) # mask respose under horizon

        factor = 1.0e-60

        # print (np.sinc(self.width * nu / lmbda) * np.sinc(factor * nv / lmbda)).shape
        # print nz.shape

        return np.sinc(self.width * nu / lmbda) * np.sinc(factor * nv / lmbda) * nz


class Antenna(ap.pol.Antenna):
    """Representation of an individual dish antenna or cylinder feed."""

    def __init__(self, pos, beam, phsoff={'x':[0.0, 0.0], 'y':[0.0, 0.0]}, bp_r={'x': np.array([1.0]), 'y': np.array([1.0])}, bp_i={'x': np.array([0.0]), 'y': np.array([0.0])}, amp={'x': 1.0, 'y': 1.0}, pointing=(0.0, np.pi/2, 0.0), **kwargs):

        x, y, z = pos
        ap.pol.Antenna.__init__(self, x, y, z, beam, phsoff, bp_r, bp_i, amp, pointing, **kwargs)


class DishAntenna(Antenna):
    """Representation of an individual dish antenna."""

    def __init__(self, pos, freqs, diameter=6.0, phsoff={'x':[0.0, 0.0], 'y':[0.0, 0.0]}, bp_r={'x': np.array([1.0]), 'y': np.array([1.0])}, bp_i={'x': np.array([0.0]), 'y': np.array([0.0])}, amp={'x': 1.0, 'y': 1.0}, pointing=(0.0, np.pi/2, 0.0), **kwargs):

        beam = DishBeam(freqs, diameter)
        Antenna.__init__(self, pos, beam, phsoff, bp_r, bp_i, amp, pointing, **kwargs)


class CylinderFeed(Antenna):
    """Representation of an individual cylinder feed."""

    # NOTE: for cylinder, x dipole along east-west, y-dipole along north-south, so for x dipole, pointing is (np.pi/2, np.pi/2, 0.0)
    def __init__(self, pos, freqs, width=15.0, length=40.0, phsoff={'x':[0.0, 0.0], 'y':[0.0, 0.0]}, bp_r={'x': np.array([1.0]), 'y': np.array([1.0])}, bp_i={'x': np.array([0.0]), 'y': np.array([0.0])}, amp={'x': 1.0, 'y': 1.0}, pointing=(np.pi/2, np.pi/2, 0.0), **kwargs):

        beam = CylinderBeam(freqs, width, length)
        Antenna.__init__(self, pos, beam, phsoff, bp_r, bp_i, amp, pointing, **kwargs)


class AntennaArray(ap.pol.AntennaArray):
    """Representation of an antenna array."""

    pass



if __name__ == '__main__':
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    xs = np.linspace(-1.0, 1.0, 2000)
    xz = np.array([ np.array([x, 0.0, (1.0-x**2)**0.5]) for x in xs ])
    x_ang = np.degrees(np.arctan2(xz[:, 2], xz[:, 0]))

    ys = np.linspace(-1.0, 1.0, 2000)
    yz = np.array([ np.array([0.0, y, (1.0-y**2)**0.5]) for y in ys ])
    y_ang = np.degrees(np.arctan2(yz[:, 2], yz[:, 1]))

    cyl_beam = CylinderBeam([750.0, 760.0], 15.0, 40.0)
    x_resp = cyl_beam.response(xz.T)
    y_resp = cyl_beam.response(yz.T)

    x_inds = np.where(x_resp>=0.5)[1]
    x_ind1, x_ind2 = x_inds[0], x_inds[-1]
    y_inds = np.where(y_resp>=0.5)[1]
    y_ind1, y_ind2 = y_inds[0], y_inds[-1]

    print x_resp.shape
    print y_resp.shape
    print x_ang[x_ind1], x_ang[x_ind2]
    print y_ang[y_ind1], y_ang[y_ind2]

    # 1d plot
    plt.figure()
    plt.plot(x_ang, x_resp[0], 'r', label='East-West')
    # plt.axvline(x=x_ang[x_ind1], linewidth=0.5, color='r')
    # plt.axvline(x=x_ang[x_ind2], linewidth=0.5, color='r')
    plt.plot(y_ang, y_resp[0], 'g', label='North-South')
    plt.axvline(x=y_ang[y_ind1], linewidth=0.5, color='g')
    plt.axvline(x=y_ang[y_ind2], linewidth=0.5, color='g')
    plt.legend()
    plt.savefig('cy.png')
    plt.clf()

    # xs = np.linspace(-1.0, 1.0, 2000)
    xs = np.linspace(-0.3, 0.3, 2000)
    ys = np.linspace(-1.0, 1.0, 2000)
    xx, yy = np.meshgrid(xs, ys)
    zs2 = 1.0 - xx**2 -yy**2
    zs = np.where(zs2>=0.0, zs2**0.5, np.nan)
    xyz = np.array([xx, yy, zs])
    resp = cyl_beam.response(xyz)
    print resp.shape

    # 2d plot
    plt.figure()
    plt.imshow(resp[0], origin='lower')
    plt.colorbar()
    plt.savefig('cy2.png')
    plt.clf()
