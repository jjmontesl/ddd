This texture was packed manually. 

Original symbols from: https://github.com/yopaseopor/traffic_signs_kendzi3D
gathered and processed by 'yopaseopor'.

Note: this texture was packed manually using PyTexturePacker. Next
time it needs to be generated it should be done using ddd atlas packing
tool.

    from PyTexturePacker import Packer

    def pack_test():
        # create a MaxRectsBinPacker
        packer = Packer.create(max_width=2048, max_height=2048, bg_color=0xffffff00)
        # pack texture images under directory "test_case/" and name the output images as "test_case".
        # "%d" in output file name "test_case%d" is a placeholder, which is a multipack index, starting with 0.
        packer.pack("es/", "traffic_signs_es_%d")
        
    pack_test()


