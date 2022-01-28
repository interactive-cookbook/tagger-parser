// Transformer model
local model_name = 'facebook/bart-large';
local transformer_embedding_dim = 1024;
local max_length = 128;

// CRF
local crf_dropout = 0.5;

// LSTM
local lstm_input_size = transformer_embedding_dim;
local lstm_bidirectional = true;
local lstm_num_layers = 2;
local lstm_hidden_size = 200;
local lstm_dropout = 0.5;

// trainer
local optimizer = 'adam';
local lr = 0.0001;
local num_epochs = 75;
local grad_norm = 10.0;
local cuda_device = 1;
local patience = 50;

local batch_size = 10;

// change to false to disable sanity checks
local sanity_check = false;

{
  dataset_reader: {
    type: 'conll2003',
    tag_label: 'ner',
    coding_scheme: 'BIOUL',
    // token_indexers: {
    //   tokens: {
    //     type: 'pretrained_transformer_mismatched',
    //     model_name: model_name,
    //     max_length: max_length,
    //   },
    // },
    token_indexers: {
      tokens: {
        type: 'pretrained_transformer_mismatched',
        model_name: model_name,
        max_length: max_length,
      },
    },
  },
  datasets_for_vocab_creation: ['train'],
  train_data_path: '/proj/cookbook/interactive-cookbook/data/English/Tagger/train.conll03',
  validation_data_path: '/proj/cookbook/interactive-cookbook/data/English/Tagger/dev.conll03',
  test_data_path: '/proj/cookbook/interactive-cookbook/data/English/Tagger/test.conll03',
  evaluate_on_test: true,
  model: {
    type: 'crf_tagger',
    label_encoding: 'BIOUL',
    dropout: crf_dropout,
    text_field_embedder: {
    // using custom mismatched embedder
      token_embedders: {
        tokens: {
          type: 'custom_pretrained_transformer_mismatched',
          model_name: model_name,
          max_length: max_length,
          sub_module: 'encoder',
        },
      },
    },
    encoder: {
        type: 'lstm',
        input_size: lstm_input_size,
        hidden_size: lstm_hidden_size,
        bidirectional: lstm_bidirectional,
        num_layers: lstm_num_layers,
        dropout: lstm_dropout,
    },
    regularizer: {
      regexes: [
        [
          'scalar_parameters',
          {
            type: 'l2',
            alpha: 0.1,
          },
        ]
      ]
    },
  },
  data_loader: {
    batch_size: batch_size,
  },
  trainer: {
    optimizer: {
      type: optimizer,
      lr: lr,
    },
    checkpointer: {
      num_serialized_models_to_keep: 1,
    },
    validation_metric: '+accuracy',
    num_epochs: num_epochs,
    grad_norm: grad_norm,
    patience: patience,
    cuda_device: cuda_device,
    enable_default_callbacks: sanity_check,
  }
}