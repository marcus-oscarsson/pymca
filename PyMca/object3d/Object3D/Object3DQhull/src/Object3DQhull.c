#include <Python.h>
#include <stdlib.h>
#include <stdio.h>

#include <./numpy/arrayobject.h>

#include "qhull.h"
#include "qset.h"		/* for FOREACHneighbor_() */
#include "poly.h"		/* for qh_vertexneighbors() */

/* Doc strings */
#if (REALfloat == 1)
PyDoc_STRVAR(Object3DQhull__doc__,
"Object3DQhullf is just an interface module to the Qhull library.\n"
"    For the time being only delaunay triangulation is implemented.\n"
"    See http://www.qhull.org for Qhull details.\n"
"\n"
"Object3DQHullf.delaunay(nodes, \"qhull  d Qbb QJ Qc Po\")\n"
"    Nodes is a sequence of points (an nrows x 2 or an nrows x 3 array)\n" 
"    The second argument is optional.\n"
"    The output is an array of indices for the facets.\n");
PyDoc_STRVAR(Object3DQhull_delaunay__doc__,
"delaunay(nodes, \"qhull  d Qbb QJ Qc Po\")\n"
"    Nodes is a sequence of points (an nrows x 2 or an nrows x 3 array)\n" 
"    The second argument is optional.\n"
"    http://www.qhull.org for Qhull details.\n"
"    The output is an array of indices for the facets.\n");
#else
PyDoc_STRVAR(Object3DQhull__doc__,
"Object3DQhull is just an interface module to the Qhull library.\n"
"    For the time being only delaunay triangulation is implemented.\n"
"    See http://www.qhull.org for Qhull details.\n"
"\n"
"Object3DQHull.delaunay(nodes, \"qhull  d Qbb QJ Qc\")\n"
"    Nodes is a sequence of points (an nrows x 2 or an nrows x 3 array)\n" 
"    The second argument is optional.\n"
"    The output is an array of indices for the facets.\n");
PyDoc_STRVAR(Object3DQhull_delaunay__doc__,
"delaunay(nodes, \"qhull  d Qbb QJ Qc\")\n"
"    Nodes is a sequence of points (an nrows x 2 or an nrows x 3 array)\n" 
"    The second argument is optional.\n"
"    http://www.qhull.org for Qhull details.\n"
"    The output is an array of indices for the facets.\n");
#endif


/* static variables */
static PyObject *Object3DQhullError;

/* Function declarations */
static PyObject *object3DDelaunay(PyObject *dummy, PyObject *args);
static void qhullResultFailure(int);
static PyObject *getQhullVersion(PyObject *dummy, PyObject *args);


static PyObject *object3DDelaunay(PyObject *self, PyObject *args)
{
	/* input parameters */
	PyObject	*input1;
        const char      *input2 = NULL;	

	/* local variables */
	PyArrayObject	*pointArray;
	PyArrayObject	*result;

	coordT		*points;	/* Qhull */
	int		dimension;	/* Qhull */
	int		nPoints;	/* Qhull */
	int		qhullResult;	/* Qhull exit code, 0 means no error */
	boolT ismalloc = False;		/* True if Qhull should free points in
								   qh_freeqhull() or reallocation */
	//char cQhullDefaultFlags[] = "qhull d Qbb Qt"; /* Qhull flags (see doc)*/
#if (REALfloat == 1)
    char cQhullDefaultFlags[] = "qhull d Qbb QJ Qc Po"; /* Qhull flags (see doc) Po is to ignore precision errors*/
#else
	char cQhullDefaultFlags[] = "qhull d Qbb QJ Qc"; /* Qhull flags (see doc)*/
#endif
    char *cQhullFlags;
	
	int			nFacets = 0;
	npy_intp	outDimensions[3];
	facetT *facet;		/* needed by FORALLfacets */
	vertexT *vertex, **vertexp;
	int j;
#if (REALfloat == 1)
	float *p;
#else
	double *p;
#endif
	unsigned int *uintP;


    /* ------------- statements ---------------*/
    if (!PyArg_ParseTuple(args, "O|z", &input1, &input2))
	{
	    PyErr_SetString(Object3DQhullError, "Unable to parse arguments");
        return NULL;
	}

	/* The array containing the points */
#if (REALfloat == 1)
	pointArray = (PyArrayObject *)
    				PyArray_ContiguousFromAny(input1, PyArray_FLOAT,2,2);
#else
	pointArray = (PyArrayObject *)
    				PyArray_ContiguousFromAny(input1, PyArray_DOUBLE,2,2);
#endif
    if (pointArray == NULL)
	{
	    PyErr_SetString(Object3DQhullError, "First argument is not a nrows x X array");
        return NULL;
	}
        if (input2 == NULL)
	{
		cQhullFlags = &cQhullDefaultFlags[0];
	}
	else
	{
		cQhullFlags = (char *) input2;
	}
	/* printf("flags = %s\n", cQhullFlags); */
	
	/* dimension to pass to Qhull */
	dimension = pointArray->dimensions[1];

	/* number of points for Qhull */
	nPoints = pointArray->dimensions[0];

	/* the points themselves for Qhull */
	points = (coordT *) pointArray->data;

	qhullResult = qh_new_qhull(dimension, nPoints, points,
				ismalloc, cQhullFlags, NULL, stderr);

	if (qhullResult)
	{
		/* Free the memory allocated by Qhull */
		qh_freeqhull(qh_ALL);
		Py_DECREF (pointArray);
		qhullResultFailure(qhullResult);
		return NULL;
	}

	/* Get the number of facets */
	/* Probably there is a better way to do it */
	FORALLfacets {
		if (facet->upperdelaunay)
			continue;
		nFacets ++;
	}
	/* printf("Number of facets = %d\n", nFacets); */

	/* Allocate the memory for the output array */
	if (0)	// As triangles
	{
		/* It has the form: [nfacets, dimension, 3] */
		outDimensions[0] = nFacets;
		outDimensions[1] = 3;
		outDimensions[2] = dimension;
		result = (PyArrayObject *)
    					PyArray_SimpleNew(3, outDimensions, PyArray_FLOAT);
		if (result == NULL)
		{
			qh_freeqhull(qh_ALL);
			Py_DECREF (pointArray);
			PyErr_SetString(Object3DQhullError, "Error allocating output memory");
			return NULL;
		}
#if (REALfloat == 1)
		p = (float *) result->data;
#else
		p = (double *) result->data;
#endif
		FORALLfacets {
			if (facet->upperdelaunay)
				continue;
			FOREACHvertex_(facet->vertices)	{
				for (j = 0; j < (qh hull_dim - 1); ++j) {
					*p =  vertex->point[j];
					++p;
				}
			}
		}
	}
	else // As indices
	{
		outDimensions[0] = nFacets;
		outDimensions[1] = 3;
		result = (PyArrayObject *)
    					PyArray_SimpleNew(2, outDimensions, PyArray_UINT32);
		if (result == NULL)
		{
			qh_freeqhull(qh_ALL);
			Py_DECREF (pointArray);
			PyErr_SetString(Object3DQhullError, "Error allocating output memory");
			return NULL;
		}

		uintP = (unsigned int *) result->data;
		FORALLfacets {
			if (facet->upperdelaunay)
				continue;
			FOREACHvertex_(facet->vertices)	{
					*uintP =  qh_pointid(vertex->point);
					++uintP;
			}
		}
	}



	/* Free the memory allocated by Qhull */
	qh_freeqhull(qh_ALL);
	 
	Py_DECREF (pointArray);

	return PyArray_Return(result);
}


static void
qhullResultFailure(int qhull_exitcode)
{
	switch (qhull_exitcode) {
	case qh_ERRinput:
		PyErr_BadInternalCall ();
		break;
	case qh_ERRsingular:
		PyErr_SetString(PyExc_ArithmeticError,
				"qhull singular input data");
		break;
	case qh_ERRprec:
		PyErr_SetString(PyExc_ArithmeticError,
				"qhull precision error");
		break;
	case qh_ERRmem:
		PyErr_NoMemory();
		break;
	case qh_ERRqhull:
		PyErr_SetString(PyExc_StandardError,
				"qhull internal error");
		break;
	}
}

static PyObject *getQhullVersion(PyObject *self, PyObject *args)
{
    return PyString_FromString(qh_version);
}

/* Module methods */
static PyMethodDef Object3DQhullMethods[] = {
	{"delaunay", object3DDelaunay, METH_VARARGS, Object3DQhull_delaunay__doc__},
    {"version",  getQhullVersion, METH_VARARGS},
	{NULL, NULL, 0, NULL} /* sentinel */
};


/* Initialise the module. */
#if (REALfloat == 1)
PyMODINIT_FUNC
initObject3DQhullf(void)
{
	PyObject	*m, *d;
	/* Create the module and add the functions */
	m = Py_InitModule3("Object3DQhullf", Object3DQhullMethods, Object3DQhull__doc__);
	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);

	import_array()
	Object3DQhullError = PyErr_NewException("Object3DQhullf.error", NULL, NULL);
	PyDict_SetItemString(d, "error", Object3DQhullError);
}
#else
PyMODINIT_FUNC
initObject3DQhull(void)
{
	PyObject	*m, *d;
	/* Create the module and add the functions */
	m = Py_InitModule3("Object3DQhull", Object3DQhullMethods, Object3DQhull__doc__);
	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);

	import_array()
	Object3DQhullError = PyErr_NewException("Object3DQhull.error", NULL, NULL);
	PyDict_SetItemString(d, "error", Object3DQhullError);
}
#endif