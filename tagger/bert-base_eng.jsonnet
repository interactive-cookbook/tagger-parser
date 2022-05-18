// CUDA
local cuda_device = 0;

// Transformer model info
local model_name = 'dslim/bert-base-NER';
local transformer_embedding_dim = 768;
local max_length = 512;

// LSTM
local lstm_input_size = transformer_embedding_dim;
local lstm_bidirectional = true;
local lstm_num_layers = 2;
local lstm_hidden_size = 200;
local lstm_dropout = 0.15;

// CRF
local crf_dropout = 0.15;

// trainer
local optimizer = 'adam';
local lr = 2e-5;
local num_epochs = 150;
// local grad_norm = 10.0;
local patience = 20;

// data loader
local batch_size = 10;

// Gradient accumulation
local num_gradient_accumulation_steps = 1;
// Gradient checkpointing
local gradient_checkpointing = true;

// data paths
local train_data_path = '/local/siyutao/tagger-parser/data/English/Tagger/train.conll03';
local validation_data_path = '/local/siyutao/tagger-parser/data/English/Tagger/dev.conll03';
local test_data_path = '/local/siyutao/tagger-parser/data/English/Tagger/test.conll03';

// change to false to disable sanity checks
local sanity_check = false;

{
  dataset_reader: {
    type: 'conll2003',
    tag_label: 'ner',
    // convert_to_coding_scheme: 'BIOUL',
    token_indexers: {
      tokens: {
        type: 'pretrained_transformer_mismatched',
        model_name: model_name,
        max_length: max_length,
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
    label_encoding: 'BIO',
    dropout: crf_dropout,
    // calculate_span_f1: true,
    text_field_embedder: {
      token_embedders: {
        tokens: {
          type: 'pretrained_transformer_mismatched',
          // uncomment to custom mismatched embedder
          // type: 'custom_pretrained_transformer_mismatched',
          // sub_module: 'encoder',
          model_name: model_name,
          max_length: max_length,
          gradient_checkpointing: gradient_checkpointing,
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
    // regularizer: {
    //   regexes: [
    //     [
    //       'scalar_parameters',
    //       {
    //         type: 'l2',
    //         alpha: 0.1,
    //       },
    //     ]
    //   ]
    // },
  },
  data_loader: {
    batch_sampler: {
      type: "bucket",
      batch_size : 10
    }
  },
  trainer: {
    optimizer: {
      type: optimizer,
      lr: lr,
    },
    checkpointer: {
      keep_most_recent_by_count: 1,
    },
    validation_metric: '+f1-measure-overall',
    num_epochs: num_epochs,
    // grad_norm: grad_norm,
    patience: patience,
    cuda_device: cuda_device,
    num_gradient_accumulation_steps: num_gradient_accumulation_steps,
    run_confidence_checks: sanity_check,
  },
}