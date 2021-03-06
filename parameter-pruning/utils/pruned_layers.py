from keras import backend as K
from keras.utils.conv_utils import conv_output_length
from keras.engine.topology import Layer


class pruned_Dense(Layer):
    def __init__(self, output_neurons, **kwargs):
        self.num_output = output_neurons
        self.dtype = 'float32'
        super(pruned_Dense, self).__init__(**kwargs)

    def build(self, input_shape):
        num_input = input_shape[1]
        shape = (num_input, self.num_output)

        # initialize the weight matrix and bias, i.e., trainable variables
        self.weight = self.add_weight(shape=shape, initializer="glorot_normal", dtype=self.dtype,
                                      name='weight', trainable=True)
        self.bias = self.add_weight(shape=(self.num_output,), initializer="zeros", name='bias', trainable=True)

        self.trainable_weights = [self.weight, self.bias]

        # non-trainable weight for pruning (only 0 or 1, where 0 is for pruning)
        self.mask = self.add_weight(shape=shape, initializer="ones", dtype=self.dtype, name='mask', trainable=False)

        super(pruned_Dense, self).build(input_shape)

    def call(self, x):
        # forward pass of layer
        pruned_weight = self.weight * self.mask
        out = K.dot(x, pruned_weight) + self.bias
        return out

    def compute_output_shape(self, input_shape):
        # defines layers output shape
        return input_shape[0], self.num_output

    def get_mask(self):
        # get the mask values
        return K.get_value(self.mask)

    def set_mask(self, mask):
        # updates mask values for layer
        K.set_value(self.mask, mask)


class pruned_Conv2D(Layer):
    def __init__(self, filters, kernel_size, strides, padding, **kwargs):
        self.filters = filters
        self.kernel_size = kernel_size
        self.strides = strides
        self.padding = padding
        self.dtype = 'float32'
        super(pruned_Conv2D, self).__init__(**kwargs)

    def build(self, input_shape):
        shape = self.kernel_size + (input_shape[-1], self.filters)
        self.weight = self.add_weight(shape=shape, initializer="glorot_normal", dtype=self.dtype, trainable=True,
                                      name='weight')
        self.bias = self.add_weight(shape=(self.filters,), initializer="zeros", name='bias', trainable=True)
        self.trainable_weights = [self.weight, self.bias]

        self.mask = self.add_weight(shape=shape, initializer="ones", dtype=self.dtype, name='mask', trainable=False)

        super(pruned_Conv2D, self).build(input_shape)

    def call(self, x):
        # forward pass of layer
        pruned_kernel = self.weight * self.mask
        out = K.conv2d(x, pruned_kernel, strides=self.strides, padding=self.padding) + self.bias
        return out

    def compute_output_shape(self, input_shape):
        output_shape = []
        for i in range(len(self.kernel_size)):
            output_shape.append(
                conv_output_length(input_shape[1 + i], self.kernel_size[i], self.padding, self.strides[i]))
        return (None,) + tuple(output_shape) + (self.filters,)

    def get_mask(self):
        # get the mask values
        return K.get_value(self.mask)

    def set_mask(self, mask):
        # updates mask values for layer
        K.set_value(self.mask, mask)