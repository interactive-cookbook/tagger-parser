// GPU
local cuda_device = 1;

// Transformer model
local model_name = 'bert-base-multilingual-cased';
local transformer_embedding_dim = 768;
local max_length = 128;

// CRF
local crf_dropout = 0.5;

// character encoding CNN
local min_padding_length = 3;
local char_embedding_dim = 16;
local cnn_num_filters = 128;
local cnn_windows = [3];

// LSTM
local lstm_input_size = transformer_embedding_dim + cnn_num_filters;
local lstm_bidirectional = true;
local lstm_num_layers = 2;
local lstm_hidden_size = 200;
local lstm_dropout = 0.5;

// trainer
local optimizer = 'adam';
local lr = 1e-3;
local num_epochs = 100;
local grad_norm = 10.0;
local patience = 25;

// batch size
local batch_size = 30;
// Gradient accumulation
local num_gradient_accumulation_steps = 1;
// Gradient checkpointing
local gradient_checkpointing = true;
// Automatic mixed precision (AMP)
local use_amp = false;

// data paths
local train_data_path = 'data/English/Tagger/train.conll03';
local validation_data_path = 'data/English/Tagger/dev.conll03';
local test_data_path = 'data/English/Tagger/test.conll03';

// change to false to disable sanity checks
local sanity_check = true;

{
  dataset_reader: {
    type: 'conll2003',
    tag_label: 'ner',
    coding_scheme: 'BIOUL',
    token_indexers: {
      tokens: {
        type: 'pretrained_transformer_mismatched',
        model_name: model_name,
        max_length: max_length,
      },
      token_characters: {
        type: 'characters',
        min_padding_length: min_padding_length,
      },
    },
  },
  datasets_for_vocab_creation: ['train'],
  train_data_path: train_data_path,
  validation_data_path: validation_data_path,
  test_data_path: test_data_path,
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
          gradient_checkpointing: gradient_checkpointing,
          // sub_module: 'encoder',
        },
        token_characters: {
          type: 'character_encoding',
          embedding: {
            embedding_dim: char_embedding_dim,
            vocab_namespace: "token_characters",
          },
          encoder: {
            type: 'cnn',
            embedding_dim: char_embedding_dim,
            num_filters: cnn_num_filters,
            ngram_filter_sizes: cnn_windows,
            conv_layer_activation: 'relu',
          }
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
      keep_most_recent_by_count: 1,
    },
    validation_metric: '+accuracy',
    num_epochs: num_epochs,
    grad_norm: grad_norm,
    num_gradient_accumulation_steps: num_gradient_accumulation_steps,
    use_amp: use_amp,
    patience: patience,
    cuda_device: cuda_device,
    run_confidence_checks: sanity_check,
  }
}