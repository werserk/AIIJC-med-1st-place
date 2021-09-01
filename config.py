class Cfg:
    seed = 0xD153A53

    # MAIN
    model = 'DeepLabV3'

    lr = 1e-4
    epochs = 20
    train_batchsize = 10
    val_batchsize = 10

    train_size, val_size = 0.8, 0.2
    # CUSTOM
    metric = 'IoUScore'

    loss_fn = 'IoULoss'
    optimizer = 'Adam'
    # scheduler = 'OneCycleLR'

    # PATHES
    root_folder = '/mnt/c/Users/dalma/Desktop/AIIJC/CovidSeg/'

    data_folder = 'data/'
    dataset_name = 'MosMed'  # MosMed, Zenodo, ZenodoLungs, MedSeg,

    custom_folder = 'custom/'

    # AUGMENTATIONS AND TRANSFORMS
    pretransforms = [  # Pre-transforms
        dict(
            name="Resize",
            params=dict(
                height=512,
                width=512,
                p=1.0,
            )
        ),
    ]

    augmentations = [  # Augmentations
        dict(
            name="HorizontalFlip",
            params=dict(
                p=0.5,
            )
        )]

    posttransforms = [  # Post-transforms
        dict(
            name="Normalize",
            params=dict(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
                max_pixel_value=255.0,
            )
        )]

    # CROSS-VALIDATION
    kfold = True

    n_splits = 5
    fold_number = 1  # from 1 to n_splits
