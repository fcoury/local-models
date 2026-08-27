# Fish completions for modelctl.

function __modelctl_complete_models
    set -l scope $argv[1]
    set -l modelctl (command -v modelctl)

    test -n "$modelctl"; or return
    command "$modelctl" __complete $scope 2>/dev/null
end

function __modelctl_needs_command
    not __fish_seen_subcommand_from list status start run stop logs path endpoint doctor help
end

function __modelctl_needs_model
    set -l tokens (commandline -opc)
    set -l current (commandline -pt)

    test (count $tokens) -eq 2; or return 1
    string match -q -- '-*' "$current"; and return 1
    __fish_seen_subcommand_from status start run stop logs path endpoint doctor
end

function __modelctl_endpoint_options
    set -l tokens (commandline -opc)

    __fish_seen_subcommand_from endpoint; or return 1
    test (count $tokens) -ge 3
end

function __modelctl_harness_arguments
  set -l tokens (commandline -opc)

  test (count $tokens) -ge 3; or return 1
  test "$tokens[2]" = run; and test "$tokens[3]" = muse-glimmer-30b
end

function __modelctl_mlxfast_arguments
    set -l tokens (commandline -opc)

    test (count $tokens) -ge 3; or return 1
    test "$tokens[2]" = run; and test "$tokens[3]" = qwen3.8-27b-mlxfast-mtp
end

function __modelctl_mlxfast_server_arguments
    set -l tokens (commandline -opc)

    test (count $tokens) -ge 3; or return 1
    test "$tokens[2]" = run; and test "$tokens[3]" = qwen3.8-27b-mlxfast-mtp-server
end

function __modelctl_no_file_completion
    set -l tokens (commandline -opc)

    test (count $tokens) -le 2; and return 0
    __fish_seen_subcommand_from run; and return 1
    return 0
end

# Keep command and model positions focused, while preserving path completion
# for runner arguments such as `modelctl run muse-glimmer-30b --root ...`.
complete -c modelctl -n __modelctl_no_file_completion -f

complete -c modelctl -n __modelctl_needs_command -f -a list -d 'Show all model services and assets'
complete -c modelctl -n __modelctl_needs_command -f -a status -d 'Show all statuses, or one model status'
complete -c modelctl -n __modelctl_needs_command -f -a start -d 'Start a model server in the background'
complete -c modelctl -n __modelctl_needs_command -f -a run -d 'Run a model server or harness in the foreground'
complete -c modelctl -n __modelctl_needs_command -f -a stop -d 'Stop a server started by modelctl'
complete -c modelctl -n __modelctl_needs_command -f -a logs -d 'Follow a model server log'
complete -c modelctl -n __modelctl_needs_command -f -a path -d 'Print the canonical model path'
complete -c modelctl -n __modelctl_needs_command -f -a endpoint -d 'Print OpenAI-compatible endpoint metadata'
complete -c modelctl -n __modelctl_needs_command -f -a doctor -d 'Validate models and their runtimes'
complete -c modelctl -n __modelctl_needs_command -f -a help -d 'Show help'
complete -c modelctl -n __modelctl_needs_command -f -s h -l help -d 'Show help'

complete -c modelctl -n '__modelctl_needs_model; and __fish_seen_subcommand_from status path doctor' \
    -f -a '(__modelctl_complete_models models)'
complete -c modelctl -n '__modelctl_needs_model; and __fish_seen_subcommand_from run' \
    -f -a '(__modelctl_complete_models runnable)'
complete -c modelctl -n '__modelctl_needs_model; and __fish_seen_subcommand_from start stop logs endpoint' \
    -f -a '(__modelctl_complete_models services)'

complete -c modelctl -n __modelctl_endpoint_options -f -l json -d 'Print metadata as JSON'

complete -c modelctl -n __modelctl_harness_arguments -f
complete -c modelctl -n __modelctl_harness_arguments -s h -l help -d 'Show harness help'
complete -c modelctl -n __modelctl_harness_arguments -f -l model -r \
    -a '(__fish_complete_path)' -d 'Model checkpoint path for the harness'
complete -c modelctl -n __modelctl_harness_arguments -f -l root -r \
    -a '(__fish_complete_directories)' -d 'Project directory for the harness'
complete -c modelctl -n __modelctl_harness_arguments -f -l task -r -d 'Task prompt for the harness'
complete -c modelctl -n __modelctl_harness_arguments -f -l max-steps -r \
    -a '4 8 12 16 24 32' -d 'Maximum agent steps'
complete -c modelctl -n __modelctl_harness_arguments -f -l max-new-tokens -r \
    -a '256 512 1024 2048' -d 'Maximum generated tokens per step'

complete -c modelctl -n __modelctl_mlxfast_arguments -f -a '--local-iterate' \
    -d 'Run the short local MTP correctness/timing loop'
complete -c modelctl -n __modelctl_mlxfast_arguments -f -a '--local-submit' \
    -d 'Run the longer local MTP pre-submit loop'
complete -c modelctl -n __modelctl_mlxfast_arguments -f -s h -l help \
    -d 'Show MLX.fast harness help'

complete -c modelctl -n __modelctl_mlxfast_server_arguments -f -a '--build' \
    -d 'Build the native Swift server adapter'
complete -c modelctl -n __modelctl_mlxfast_server_arguments -f -a '--doctor' \
    -d 'Validate the native Swift server adapter'
complete -c modelctl -n __modelctl_mlxfast_server_arguments -f -s h -l help \
    -d 'Show MLX.fast server help'
